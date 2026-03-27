"""
src/retriever/ingest.py

Multi-Engine Ingestion Pipeline — xây dựng FAISS index cho engine được chọn.

Cả hai engine đều:
  1. Đọc dental_dataset_v2.json (hoặc dental_dataset.json nếu v2 chưa có)
  2. Ghép title + section + summary + content thành chuỗi ngữ nghĩa phong phú
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

from src.config import RAW_DATA_PATH, RAW_DATA_V2_PATH, PROCESSED_DATA_PATH, VECTOR_DB_DIR
from src.retriever.engines import create_engine, EmbeddingEngine


# Ingest
# Shared helpers

# Load dataset
def _load_dataset(path: Path) -> list[dict]:
    """Đọc file JSON gốc, trả về danh sách document dicts."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Build text for embedding
def _build_text_for_embedding(doc: dict) -> str:
    """
    Ghép title + section + summary + content thành chuỗi duy nhất.

    VD: "Tiêu đề: Sâu răng | Mục: Nguyên nhân | Tóm tắt: ... | Nội dung: ..."
    """
    title = doc.get("title", "").strip()
    section = doc.get("section", "").strip()
    summary = doc.get("summary", "").strip()
    content = doc.get("content", "").strip()

    parts: list[str] = []
    if title:
        parts.append(f"Tiêu đề: {title}")
    if section:
        parts.append(f"Mục: {section}")
    if summary:
        parts.append(f"Tóm tắt: {summary}")
    if content:
        parts.append(f"Nội dung: {content}")
    return " | ".join(parts)


def _save_json(data: list | dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)



# Pipeline chính

def build_faiss_index(engine_name: str) -> None:
    # Tạo engine
    engine: EmbeddingEngine = create_engine(engine_name)
    # Tạo output directory
    output_dir: Path = VECTOR_DB_DIR / engine.name

    # In log
    print(f"{'=' * 60}")
    print(f"  PIPELINE XÂY DỰNG FAISS INDEX — Engine: {engine.name.upper()}")
    print(f"  Số chiều vector: {engine.dimension}  |  Thư mục output: {output_dir}")
    print(f"{'=' * 60}")

    # Load dataset (ưu tiên v2 nếu tồn tại)
    dataset_path = RAW_DATA_V2_PATH if RAW_DATA_V2_PATH.exists() else RAW_DATA_PATH
    print(f"\n[1/4] Tải tập dữ liệu: {dataset_path}")
    data = _load_dataset(dataset_path)
    print(f"      -> {len(data)} tài liệu đã được tải.")

    # Prepare texts
    print(f"\n[2/4] Chuẩn bị văn bản...")
    texts: list[str] = []
    metadata: list[dict] = []

    for doc in tqdm(data, desc="  Xây dựng văn bản", unit="doc"):
        texts.append(_build_text_for_embedding(doc))
        metadata.append(doc)

    # Encode vectors
    print(f"\n[3/4] Encode {len(texts)} tài liệu với engine '{engine.name}'...")
    # Encode vectors
    vectors: np.ndarray = engine.embed_batch(texts)
    actual_dim = vectors.shape[1]

    if actual_dim != engine.dimension:
        print(
            f"      CẢNH BÁO: số chiều thực tế ({actual_dim}) khác với "
            f"cấu hình ({engine.dimension}). Sử dụng số chiều thực tế."
        )

    # Build FAISS index & save
    print(f"\n[4/4] Xây dựng FAISS IndexFlatIP (dim={actual_dim})...")
    index = faiss.IndexFlatIP(actual_dim)
    index.add(vectors)
    print(f"      -> {index.ntotal} vector đã được index.")

    index_path = output_dir / "faiss.index"
    metadata_path = output_dir / "metadata.json"

    output_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    print(f"      -> Index FAISS  : {index_path}")

    _save_json(metadata, metadata_path)
    print(f"      -> Metadata đã xử lý: {metadata_path}")

    _save_json(metadata, PROCESSED_DATA_PATH)
    print(f"      -> Chunks đã xử lý: {PROCESSED_DATA_PATH}")

    print(f"\n{'=' * 60}")
    print(f"  DONE! {len(metadata)} tài liệu đã được index với engine '{engine.name}'.")
    print(f"{'=' * 60}")


# Command Line Interface

def main() -> None:
    # Tạo parser
    parser = argparse.ArgumentParser(
        description="Pipeline xây dựng FAISS index cho engine được chọn.",
        epilog=(
            "Ví dụ:\n"
            "  python -m src.retriever.ingest --engine local\n"
            "  python -m src.retriever.ingest --engine openai\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Thêm argument
    parser.add_argument(
        "--engine",
        choices=["openai", "local"],
        default="local",
        help="Engine embedding (default: local)",
    )
    args = parser.parse_args()
    # Build FAISS index
    # Chạy pipeline
    build_faiss_index(engine_name=args.engine)


if __name__ == "__main__":
    main()
