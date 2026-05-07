# src/retriever/search.py
"""
Hybrid Search v4: Multi-Query Expansion + FAISS + BM25 + RRF.

Kiến trúc:
  - EmbeddingEngine (Strategy Pattern) xử lý việc embed query.
  - Retriever nhận engine name tại __init__, tự động load đúng FAISS index
    và model tương ứng từ vector_db/{engine}/.
  - Multi-Query: dùng LLM sinh 2 câu hỏi biến thể → search cả 3
    → merge điểm RRF → tăng recall, tránh sót do khác biệt từ khóa.
  - Toàn bộ logic BM25, RRF scoring, category pre-filtering, dynamic weights
    hoạt động ĐỒNG NHẤT bất kể engine nào → dễ so sánh hiệu năng.

Chuyển đổi engine chỉ cần thay đổi biến EMBEDDING_ENGINE trong .env:
  EMBEDDING_ENGINE=local   → dùng vietnamese-sbert (768-dim, miễn phí)
  EMBEDDING_ENGINE=openai  → dùng text-embedding-3-small (1536-dim, trả phí)
"""

import json
import logging
import re
import time
from pathlib import Path

import faiss

logger = logging.getLogger(__name__)
import numpy as np
from openai import OpenAI
from rank_bm25 import BM25Okapi
from underthesea import word_tokenize

from src.config import (
    VECTOR_DB_DIR,
    EMBEDDING_ENGINE,
    LLM_ENGINE,
    OPENAI_API_KEY,
    OPENAI_CHAT_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_MODEL,
    TOP_K,
)
from src.retriever.engines import create_engine, EmbeddingEngine
from src.lib.constants import EXPAND_QUERY_SYSTEM_PROMPT

# Retriever
# Khởi tạo Retriever
class Retriever:
    # RRF_K
    _RRF_K: int = 60
    # RRF_MISS_RANK
    _RRF_MISS_RANK: int = 1000
    # KEYWORD_HEAVY_SIGNALS
    _KEYWORD_HEAVY_SIGNALS: list[str] = [
        "chi phí", "bảng giá", "giá bao nhiêu", "bao nhiêu tiền",
        "giá cả", "giá tiền", "phí",
        "quy trình", "các bước", "trình tự", "thứ tự",
        "mất bao lâu", "thời gian",
    ]

    # Khởi tạo Retriever
    def __init__(
        self,
        engine: str = EMBEDDING_ENGINE,
        llm_engine: str = LLM_ENGINE,
    ) -> None:
        # Khởi tạo engine name
        self.engine_name: str = engine
        # Khởi tạo embedder
        self._embedder: EmbeddingEngine = create_engine(engine)

        # Load FAISS index + metadata
        db_dir: Path = VECTOR_DB_DIR / engine
        index_path = db_dir / "faiss.index"
        metadata_path = db_dir / "metadata.json"

        # Nếu index không tồn tại, raise error
        if not index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found at: {index_path}\n"
                f"Please run: python -m src.retriever.ingest --engine {engine}"
            )

        # Load index
        self.index: faiss.Index = faiss.read_index(str(index_path))

        # Load metadata
        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata: list[dict] = json.load(f)

        # Khởi tạo disease set
        self._disease_set: list[str] = sorted(
            {doc.get("metadata", {}).get("disease", "") for doc in self.metadata} - {""}
        )

        # --- BM25 ---
        # Khởi tạo BM25
        enriched_corpus = [
            f"{doc.get('title', '')} {doc.get('section', '')} {doc.get('summary', '')} {doc.get('content', '')}"
            for doc in self.metadata
        ]
        tokenized_corpus = [self.normalize_and_tokenize(text) for text in enriched_corpus]
        # Khởi tạo BM25
        self.bm25 = BM25Okapi(tokenized_corpus)

        # Khởi tạo LLM client (cho multi-query expansion)
        self._init_llm_client(llm_engine)

    # LLM client init

    def _init_llm_client(self, llm_engine: str) -> None:
        try:
            if llm_engine == "openai":
                self._llm = OpenAI(api_key=OPENAI_API_KEY)
                self._llm_model = OPENAI_CHAT_MODEL
            else:
                self._llm = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
                self._llm_model = OLLAMA_CHAT_MODEL
        except Exception:
            self._llm = None
            self._llm_model = None

    # Public API

    def get_available_diseases(self) -> list[str]:
        return self._disease_set

    # Text normalization & tokenization (underthesea)

    def normalize_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        return " ".join(text.split())

    def normalize_and_tokenize(self, text: str) -> list[str]:
        """Tokenize tiếng Việt: "niềng răng" → "niềng_răng" (1 token duy nhất)."""
        clean = self.normalize_text(text)
        return word_tokenize(clean, format="text").split()

    # Embedding (delegate cho engine)

    def embed_query(self, query: str) -> np.ndarray:
        return self._embedder.embed_query(query)

    # Multi-Query Expansion

    def expand_queries(self, query: str) -> list[str]:
        """
        Dùng LLM sinh 2 câu biến thể từ query gốc.
        Trả về [query_gốc, variant_1, variant_2].
        Nếu LLM lỗi → fallback chỉ trả query gốc.
        """
        if not self._llm:
            return [query]

        try:
            resp = self._llm.chat.completions.create(
                model=self._llm_model,
                messages=[
                    {"role": "system", "content": EXPAND_QUERY_SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                temperature=0.5,
                max_tokens=200,
            )
            raw = resp.choices[0].message.content.strip()
            variants = [line.strip().lstrip("- ").strip() for line in raw.splitlines() if line.strip()]
            variants = [v for v in variants[:2] if v]
            return [query] + variants

        except Exception:
            return [query]

    # Category Pre-filtering

    def _match_categories(self, categories: list[str] | None) -> set[int] | None:
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

    # Dynamic weight detection

    def _is_keyword_heavy(self, query: str) -> bool:
        q_lower = query.lower()
        return any(signal in q_lower for signal in self._KEYWORD_HEAVY_SIGNALS)

    # Single-query hybrid scoring (FAISS + BM25 + RRF)

    def _hybrid_score(
        self,
        query: str,
        top_k: int,
        valid_indices: set[int] | None,
        w_vector: float,
        w_bm25: float,
        query_label: str = "",
    ) -> dict[int, float]:
        """Chạy FAISS + BM25 + RRF cho 1 query, trả về {doc_idx: rrf_score}."""
        tag = f" [{query_label}]" if query_label else ""

        # --- Embedding ---
        t0 = time.perf_counter()
        query_vector = np.array([self.embed_query(query)], dtype="float32")
        t_embed = time.perf_counter() - t0
        logger.info("[TIME-LOG]   Embedding%s mất: %.3fs", tag, t_embed)

        # --- FAISS ---
        t0 = time.perf_counter()
        n_search = min(top_k * 5, self.index.ntotal)
        faiss_scores, faiss_indices = self.index.search(query_vector, n_search)
        t_faiss = time.perf_counter() - t0
        logger.info("[TIME-LOG]   FAISS Search%s mất: %.3fs", tag, t_faiss)

        vector_ranked: list[int] = []
        for score, idx in zip(faiss_scores[0], faiss_indices[0]):
            if idx == -1:
                continue
            idx = int(idx)
            if valid_indices is not None and idx not in valid_indices:
                continue
            vector_ranked.append(idx)

        # --- BM25 ---
        t0 = time.perf_counter()
        query_tokens = self.normalize_and_tokenize(query)
        bm25_all_scores = self.bm25.get_scores(query_tokens)
        bm25_sorted = np.argsort(bm25_all_scores)[::-1]
        t_bm25 = time.perf_counter() - t0
        logger.info("[TIME-LOG]   BM25 Search%s mất: %.3fs", tag, t_bm25)

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

        # --- RRF ---
        all_candidates = set(vector_ranked) | set(bm25_ranked)
        if not all_candidates:
            return {}

        v_rank_map = {idx: rank for rank, idx in enumerate(vector_ranked)}
        b_rank_map = {idx: rank for rank, idx in enumerate(bm25_ranked)}

        scores: dict[int, float] = {}
        for idx in all_candidates:
            v_r = v_rank_map.get(idx, self._RRF_MISS_RANK)
            b_r = b_rank_map.get(idx, self._RRF_MISS_RANK)
            scores[idx] = (
                w_vector / (self._RRF_K + v_r + 1)
                + w_bm25 / (self._RRF_K + b_r + 1)
            )

        return scores

    # Overview boost — ưu tiên bài tổng quan lên đầu

    _OVERVIEW_SIGNALS: list[str] = [
        "tổng quan", "tìm hiểu về", "quy trình chung",
        "giới thiệu", "là gì", "các loại",
    ]

    def _boost_overview(self, results: list[dict]) -> list[dict]:
        """
        Đưa bài có section/title mang tính tổng quan lên đầu danh sách,
        giữ nguyên thứ tự tương đối trong mỗi nhóm.
        """
        overview: list[dict] = []
        rest: list[dict] = []

        for doc in results:
            title = doc.get("title", "").lower()
            section = doc.get("section", "").lower()
            combined = f"{title} {section}"

            if any(signal in combined for signal in self._OVERVIEW_SIGNALS):
                overview.append(doc)
            else:
                rest.append(doc)

        return overview + rest

    # Core Search (Multi-Query + Hybrid + RRF merge)

    def search(
        self,
        query: str,
        top_k: int = TOP_K,
        categories: list[str] | None = None,
        expanded_queries: list[str] | None = None,
    ) -> list[dict]:
        """
        Hybrid Search với Multi-Query Expansion.

        Args:
            expanded_queries: Danh sách queries đã expand sẵn từ bên ngoài.
                              Nếu None → tự gọi expand_queries() bên trong.
        """
        if not self.metadata:
            return []

        t_search_start = time.perf_counter()
        logger.info("[TIME-LOG] === RETRIEVAL START ===")

        valid_indices = self._match_categories(categories)

        if self._is_keyword_heavy(query):
            w_vector, w_bm25 = 0.3, 0.7
        else:
            w_vector, w_bm25 = 0.5, 0.5

        queries = expanded_queries if expanded_queries else self.expand_queries(query)

        merged: dict[int, float] = {}
        for i, q in enumerate(queries):
            label = "original" if i == 0 else f"variant_{i}"
            q_scores = self._hybrid_score(q, top_k, valid_indices, w_vector, w_bm25, query_label=label)
            for idx, score in q_scores.items():
                merged[idx] = merged.get(idx, 0.0) + score

        if not merged:
            return []

        ranked = sorted(merged.items(), key=lambda x: x[1], reverse=True)
        results = [self.metadata[idx] for idx, _ in ranked[:top_k]]

        t_search_total = time.perf_counter() - t_search_start
        logger.info("[TIME-LOG] === RETRIEVAL END === Tổng: %.2fs", t_search_total)

        return self._boost_overview(results)
