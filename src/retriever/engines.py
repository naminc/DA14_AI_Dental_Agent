"""
src/retriever/engines.py

Strategy Pattern cho Multi-Embedding Engine.

Hai engine được hỗ trợ:
  ┌──────────┬────────────────────────────┬──────┬───────────┐
  │ Engine   │ Model                      │ Dim  │ Chi phí   │
  ├──────────┼────────────────────────────┼──────┼───────────┤
  │ openai   │ text-embedding-3-small     │ 1536 │ ~$0.02/1M │
  │ local    │ keepitreal/vietnamese-sbert │  768 │ Miễn phí  │
  └──────────┴────────────────────────────┴──────┴───────────┘

Cả hai engine đều trả về vector đã L2-normalized, tương thích với
FAISS IndexFlatIP (Inner Product ≡ Cosine Similarity).

Usage:
    from src.retriever.engines import create_engine

    engine = create_engine("local")       # hoặc "openai"
    vector = engine.embed_query("sâu răng là gì?")
    matrix = engine.embed_batch(["text1", "text2", ...])
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from functools import lru_cache

import numpy as np
from tqdm import tqdm

from src.config import (
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_DIM,
    LOCAL_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_DIM,
)


# ---------------------------------------------------------------------------
# Abstract Base
# ---------------------------------------------------------------------------

class EmbeddingEngine(ABC):
    """Interface chung cho mọi embedding engine."""

    @abstractmethod
    def embed_query(self, query: str) -> np.ndarray:
        """Embed 1 câu query → vector float32 shape (dim,)."""

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed danh sách văn bản → matrix float32 shape (N, dim)."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Số chiều vector đầu ra."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tên engine (dùng làm tên thư mục: vector_db/{name}/)."""


# ---------------------------------------------------------------------------
# OpenAI Engine
# ---------------------------------------------------------------------------

class OpenAIEngine(EmbeddingEngine):
    """
    Embedding qua API OpenAI text-embedding-3-small (1536-dim).

    ⚠️  Yêu cầu OPENAI_API_KEY trong .env
    ⚠️  Vectors đã được normalize bởi API → dùng trực tiếp với IndexFlatIP
    """

    def __init__(self) -> None:
        from openai import OpenAI

        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is required for OpenAI embedding engine. "
                "Set it in .env or switch to EMBEDDING_ENGINE=local"
            )
        self._client = OpenAI(api_key=OPENAI_API_KEY)
        self._model = OPENAI_EMBEDDING_MODEL

    @property
    def dimension(self) -> int:
        return OPENAI_EMBEDDING_DIM

    @property
    def name(self) -> str:
        return "openai"

    def embed_query(self, query: str) -> np.ndarray:
        response = self._client.embeddings.create(model=self._model, input=query)
        return np.array(response.data[0].embedding, dtype="float32")

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """
        Batch embedding qua API.

        OpenAI cho phép tối đa 2048 inputs/request. Dùng batch_size=100
        để an toàn với rate limit Tier-1. Delay 0.3s giữa các batch.
        """
        all_embeddings: list[list[float]] = []
        batch_size = 100

        for i in tqdm(
            range(0, len(texts), batch_size),
            desc="  OpenAI Embedding",
            unit="batch",
        ):
            batch = texts[i : i + batch_size]
            response = self._client.embeddings.create(model=self._model, input=batch)
            sorted_data = sorted(response.data, key=lambda x: x.index)
            all_embeddings.extend([d.embedding for d in sorted_data])

            if i + batch_size < len(texts):
                time.sleep(0.3)

        return np.array(all_embeddings, dtype="float32")


# ---------------------------------------------------------------------------
# Local Engine (sentence-transformers)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_sbert_model():
    """
    Singleton — load model 1 lần duy nhất (~420 MB RAM).

    Chặn Thread-auto_conversion bằng env DISABLE_SAFETENSORS_CONVERSION=1.
    Thread đó luôn cố gọi HuggingFace API để check bản safetensors dù
    model đã cached — gây lỗi khi offline. Biến này được transformers
    kiểm tra tại runtime qua is_env_variable_true() (os.getenv).

    Ưu tiên local_files_only=True để load offline từ cache.
    Fallback download nếu model chưa có trong cache.
    """
    import os
    from sentence_transformers import SentenceTransformer

    os.environ["DISABLE_SAFETENSORS_CONVERSION"] = "1"

    try:
        return SentenceTransformer(LOCAL_EMBEDDING_MODEL, local_files_only=True)
    except Exception:
        print(f"[LocalEngine] Đang tải model '{LOCAL_EMBEDDING_MODEL}' từ HuggingFace lần đầu...")
        return SentenceTransformer(LOCAL_EMBEDDING_MODEL)


class LocalEngine(EmbeddingEngine):
    """
    Embedding offline bằng sentence-transformers (keepitreal/vietnamese-sbert, 768-dim).

    ⚠️  Lần đầu chạy sẽ tải model ~420 MB về ~/.cache/huggingface
    ⚠️  Model chiếm ~420 MB RAM khi load (chỉ load 1 lần qua lru_cache)
    """

    def __init__(self) -> None:
        self._model = _load_sbert_model()

    @property
    def dimension(self) -> int:
        return LOCAL_EMBEDDING_DIM

    @property
    def name(self) -> str:
        return "local"

    def embed_query(self, query: str) -> np.ndarray:
        vector: np.ndarray = self._model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return vector.astype("float32")

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """batch_size=64 cân bằng tốc độ / bộ nhớ; tăng lên 128 nếu RAM > 16 GB."""
        embeddings = self._model.encode(
            texts,
            batch_size=64,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return np.array(embeddings, dtype="float32")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_ENGINE_REGISTRY: dict[str, type[EmbeddingEngine]] = {
    "openai": OpenAIEngine,
    "local": LocalEngine,
}


def create_engine(engine_name: str) -> EmbeddingEngine:
    """
    Factory function — tạo embedding engine theo tên.

    Args:
        engine_name: "openai" hoặc "local"

    Raises:
        ValueError: nếu engine_name không hợp lệ.
    """
    engine_cls = _ENGINE_REGISTRY.get(engine_name)
    if engine_cls is None:
        valid = ", ".join(_ENGINE_REGISTRY.keys())
        raise ValueError(f"Unknown engine '{engine_name}'. Valid engines: {valid}")
    return engine_cls()
