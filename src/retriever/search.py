# src/retriever/search.py
"""
Hybrid Search v3: Multi-Engine FAISS + BM25 + Metadata Pre-filtering + RRF.

Kiến trúc:
  - EmbeddingEngine (Strategy Pattern) xử lý việc embed query.
  - Retriever nhận engine name tại __init__, tự động load đúng FAISS index
    và model tương ứng từ vector_db/{engine}/.
  - Toàn bộ logic BM25, RRF scoring, category pre-filtering, dynamic weights
    hoạt động ĐỒNG NHẤT bất kể engine nào → dễ so sánh hiệu năng.

Chuyển đổi engine chỉ cần thay đổi biến EMBEDDING_ENGINE trong .env:
  EMBEDDING_ENGINE=local   → dùng vietnamese-sbert (768-dim, miễn phí)
  EMBEDDING_ENGINE=openai  → dùng text-embedding-3-small (1536-dim, trả phí)
"""

import json
import re
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from underthesea import word_tokenize

from src.config import VECTOR_DB_DIR, EMBEDDING_ENGINE
from src.retriever.engines import create_engine, EmbeddingEngine


class Retriever:
    # RRF hyperparameters (k=60 theo paper gốc Cormack et al.)
    _RRF_K: int = 60
    _RRF_MISS_RANK: int = 1000

    _KEYWORD_HEAVY_SIGNALS: list[str] = [
        "chi phí", "bảng giá", "giá bao nhiêu", "bao nhiêu tiền",
        "giá cả", "giá tiền", "phí",
        "quy trình", "các bước", "trình tự", "thứ tự",
        "mất bao lâu", "thời gian",
    ]

    def __init__(self, engine: str = EMBEDDING_ENGINE) -> None:
        """
        Khởi tạo Retriever với engine được chọn.

        Args:
            engine: "openai" hoặc "local" (default từ config / .env).
        """
        self.engine_name: str = engine
        self._embedder: EmbeddingEngine = create_engine(engine)

        # Load FAISS index + metadata từ thư mục engine tương ứng
        db_dir: Path = VECTOR_DB_DIR / engine
        index_path = db_dir / "faiss.index"
        metadata_path = db_dir / "metadata.json"

        if not index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found at: {index_path}\n"
                f"Please run: python -m src.retriever.ingest --engine {engine}"
            )

        self.index: faiss.Index = faiss.read_index(str(index_path))

        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata: list[dict] = json.load(f)

        # Tập hợp disease duy nhất (cho entity-extraction trong chatbot)
        self._disease_set: list[str] = sorted(
            {doc.get("metadata", {}).get("disease", "") for doc in self.metadata} - {""}
        )

        # BM25 trên corpus mở rộng: title + section + content
        enriched_corpus = [
            f"{doc.get('title', '')} {doc.get('section', '')} {doc.get('content', '')}"
            for doc in self.metadata
        ]
        tokenized_corpus = [self.normalize_and_tokenize(text) for text in enriched_corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_available_diseases(self) -> list[str]:
        return self._disease_set

    # ------------------------------------------------------------------
    # Text normalization & tokenization (underthesea)
    # ------------------------------------------------------------------

    def normalize_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        return " ".join(text.split())

    def normalize_and_tokenize(self, text: str) -> list[str]:
        """
        Tokenize tiếng Việt: "niềng răng" → "niềng_răng" (1 token duy nhất).
        format="text" đảm bảo từ ghép nha khoa được giữ nguyên.
        """
        clean = self.normalize_text(text)
        return word_tokenize(clean, format="text").split()

    # ------------------------------------------------------------------
    # Embedding (delegate cho engine)
    # ------------------------------------------------------------------

    def embed_query(self, query: str) -> np.ndarray:
        """Embed query bằng engine đã chọn. Trả về vector float32 shape (dim,)."""
        return self._embedder.embed_query(query)

    # ------------------------------------------------------------------
    # Category Pre-filtering
    # ------------------------------------------------------------------

    def _match_categories(self, categories: list[str] | None) -> set[int] | None:
        """
        Trả về indices của metadata khớp category. None = full search.

        Matching 2 lớp:
          - Substring: "sâu răng" khớp "Sâu răng cửa", "Sâu răng hàm"...
          - Word-set:  "sâu răng" khớp "Răng sâu" (đảo từ)
        """
        if not categories:
            return None

        matched: set[int] = set()

        for i, doc in enumerate(self.metadata):
            disease = doc.get("metadata", {}).get("disease", "")
            if not disease:
                continue

            disease_lower = disease.lower()
            disease_words = set(disease_lower.split())

            for kw in categories:
                kw_lower = kw.lower().strip()
                if not kw_lower:
                    continue
                kw_words = set(kw_lower.split())

                if kw_lower in disease_lower or disease_lower in kw_lower:
                    matched.add(i)
                    break

                if kw_words.issubset(disease_words) or disease_words.issubset(kw_words):
                    matched.add(i)
                    break

        return matched if matched else None

    # ------------------------------------------------------------------
    # Dynamic weight detection
    # ------------------------------------------------------------------

    def _is_keyword_heavy(self, query: str) -> bool:
        q_lower = query.lower()
        return any(signal in q_lower for signal in self._KEYWORD_HEAVY_SIGNALS)

    # ------------------------------------------------------------------
    # Core Search (Hybrid + RRF)
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 7,
        categories: list[str] | None = None,
    ) -> list[dict]:
        """
        Hybrid search: FAISS vector + BM25 keyword + RRF merge.

        Flow:
            1. Pre-filter theo category (nếu có)
            2. FAISS search → ranked list
            3. BM25 search → ranked list
            4. RRF merge với dynamic weights → top_k
        """
        if not self.metadata:
            return []

        valid_indices = self._match_categories(categories)

        if self._is_keyword_heavy(query):
            w_vector, w_bm25 = 0.3, 0.7
        else:
            w_vector, w_bm25 = 0.5, 0.5

        # --- FAISS Vector Search ---
        query_vector = np.array([self.embed_query(query)], dtype="float32")
        n_search = min(top_k * 5, self.index.ntotal)
        faiss_scores, faiss_indices = self.index.search(query_vector, n_search)

        vector_ranked: list[int] = []
        for score, idx in zip(faiss_scores[0], faiss_indices[0]):
            if idx == -1:
                continue
            idx = int(idx)
            if valid_indices is not None and idx not in valid_indices:
                continue
            vector_ranked.append(idx)

        # --- BM25 Keyword Search ---
        query_tokens = self.normalize_and_tokenize(query)
        bm25_all_scores = self.bm25.get_scores(query_tokens)
        bm25_sorted = np.argsort(bm25_all_scores)[::-1]

        bm25_ranked: list[int] = []
        for idx in bm25_sorted:
            idx = int(idx)
            if bm25_all_scores[idx] <= 0:
                break
            if valid_indices is not None and idx not in valid_indices:
                continue
            bm25_ranked.append(idx)
            if len(bm25_ranked) >= top_k * 5:
                break

        # --- Reciprocal Rank Fusion ---
        all_candidates = set(vector_ranked) | set(bm25_ranked)
        if not all_candidates:
            return []

        v_rank_map = {idx: rank for rank, idx in enumerate(vector_ranked)}
        b_rank_map = {idx: rank for rank, idx in enumerate(bm25_ranked)}

        rrf_scored: list[tuple[int, float]] = []
        for idx in all_candidates:
            v_r = v_rank_map.get(idx, self._RRF_MISS_RANK)
            b_r = b_rank_map.get(idx, self._RRF_MISS_RANK)
            rrf = (
                w_vector / (self._RRF_K + v_r + 1)
                + w_bm25 / (self._RRF_K + b_r + 1)
            )
            rrf_scored.append((idx, rrf))

        rrf_scored.sort(key=lambda x: x[1], reverse=True)

        return [self.metadata[idx] for idx, _ in rrf_scored[:top_k]]
