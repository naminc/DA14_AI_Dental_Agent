from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "dental_dataset.json"
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed" / "chunks.json"

FAISS_INDEX_PATH = BASE_DIR / "data" / "embeddings" / "faiss.index"
FAISS_METADATA_PATH = BASE_DIR / "data" / "embeddings" / "metadata.json"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4.1-mini"
TOP_K = 5