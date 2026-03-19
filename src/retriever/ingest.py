"""
src/retriever/ingest.py

Multi-Engine Ingestion Pipeline — xây dựng FAISS index cho engine được chọn.

Cả hai engine đều:
  1. Đọc dental_dataset.json
  2. Ghép title + section + content thành chuỗi ngữ nghĩa phong phú
  3. Encode vectors (đã L2-normalized)
  4. Lưu vào IndexFlatIP (Inner Product ≡ Cosine Similarity)

Output được lưu tách biệt theo engine:
  data/vector_db/local/faiss.index   + metadata.json
  data/vector_db/openai/faiss.index  + metadata.json

──────────────────────────────────────────────────────────────
  Chạy cho Local engine (miễn phí, mặc định):
    python -m src.retriever.ingest --engine local

  Chạy cho OpenAI engine (cần OPENAI_API_KEY trong .env):
    python -m src.retriever.ingest --engine openai

  Chạy cả hai engine liên tiếp:
    python -m src.retriever.ingest --engine local
    python -m src.retriever.ingest --engine openai
──────────────────────────────────────────────────────────────
"""

import argparse
import json
from pathlib import Path

import faiss
import numpy as np
from tqdm import tqdm

from src.config import RAW_DATA_PATH, PROCESSED_DATA_PATH, VECTOR_DB_DIR
from src.retriever.engines import create_engine, EmbeddingEngine


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _load_dataset(path: Path) -> list[dict]:
    """Đọc file JSON gốc, trả về danh sách document dicts."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_text_for_embedding(doc: dict) -> str:
    """
    Ghép title + section + content thành chuỗi duy nhất.

    Giúp model embedding hiểu đầy đủ ngữ cảnh thay vì chỉ dựa vào content đơn lẻ.
    VD: "Tiêu đề: Sâu răng | Mục: Nguyên nhân | Vi khuẩn gây sâu răng..."
    """
    parts: list[str] = []
    if title := doc.get("title", "").strip():
        parts.append(f"Tiêu đề: {title}")
    if section := doc.get("section", "").strip():
        parts.append(f"Mục: {section}")
    if content := doc.get("content", "").strip():
        parts.append(content)
    return " | ".join(parts)


def _save_json(data: list | dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def build_faiss_index(engine_name: str) -> None:
    """
    Pipeline chính: load → prepare → encode → index → save.

    Args:
        engine_name: "openai" hoặc "local" — quyết định engine nào được dùng
                     và thư mục output (vector_db/{engine_name}/).
    """
    engine: EmbeddingEngine = create_engine(engine_name)
    output_dir: Path = VECTOR_DB_DIR / engine.name

    print(f"{'=' * 60}")
    print(f"  INGEST PIPELINE — Engine: {engine.name.upper()}")
    print(f"  Dimension: {engine.dimension}  |  Output: {output_dir}")
    print(f"{'=' * 60}")

    # --- 1. Load dataset -------------------------------------------------
    print(f"\n[1/4] Loading dataset: {RAW_DATA_PATH}")
    data = _load_dataset(RAW_DATA_PATH)
    print(f"      -> {len(data)} documents loaded.")

    # --- 2. Prepare texts ------------------------------------------------
    print(f"\n[2/4] Preparing texts...")
    texts: list[str] = []
    metadata: list[dict] = []

    for doc in tqdm(data, desc="  Build texts", unit="doc"):
        texts.append(_build_text_for_embedding(doc))
        metadata.append(doc)

    # --- 3. Encode vectors -----------------------------------------------
    print(f"\n[3/4] Encoding {len(texts)} documents with '{engine.name}' engine...")
    vectors: np.ndarray = engine.embed_batch(texts)
    actual_dim = vectors.shape[1]

    if actual_dim != engine.dimension:
        print(
            f"      WARNING: actual dim ({actual_dim}) differs from "
            f"config ({engine.dimension}). Using actual."
        )

    # --- 4. Build FAISS index & save -------------------------------------
    print(f"\n[4/4] Building FAISS IndexFlatIP (dim={actual_dim})...")
    index = faiss.IndexFlatIP(actual_dim)
    index.add(vectors)
    print(f"      -> {index.ntotal} vectors indexed.")

    index_path = output_dir / "faiss.index"
    metadata_path = output_dir / "metadata.json"

    output_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    print(f"      -> FAISS index  : {index_path}")

    _save_json(metadata, metadata_path)
    print(f"      -> Metadata     : {metadata_path}")

    _save_json(metadata, PROCESSED_DATA_PATH)
    print(f"      -> Chunks       : {PROCESSED_DATA_PATH}")

    print(f"\n{'=' * 60}")
    print(f"  DONE! {len(metadata)} documents indexed with '{engine.name}' engine.")
    print(f"{'=' * 60}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dental RAG Ingest Pipeline — build FAISS index for a chosen engine.",
        epilog=(
            "Examples:\n"
            "  python -m src.retriever.ingest --engine local\n"
            "  python -m src.retriever.ingest --engine openai\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--engine",
        choices=["openai", "local"],
        default="local",
        help="Embedding engine (default: local)",
    )
    args = parser.parse_args()
    build_faiss_index(engine_name=args.engine)


if __name__ == "__main__":
    main()
