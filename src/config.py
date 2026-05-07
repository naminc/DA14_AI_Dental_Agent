from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Data paths (shared across engines)
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "dental_dataset.json"
RAW_DATA_V2_PATH = BASE_DIR / "data" / "raw" / "dental_dataset_v2.json"
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed" / "chunks.json"

# Multi-Embedding Engine
#   EMBEDDING_ENGINE = "local"   → sentence-transformers (miễn phí, offline)
#   EMBEDDING_ENGINE = "openai"  → API text-embedding-3-small (trả phí)
EMBEDDING_ENGINE = os.getenv("EMBEDDING_ENGINE", "local")

VECTOR_DB_DIR = BASE_DIR / "data" / "vector_db"

# OpenAI config (embedding + chat)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_EMBEDDING_DIM = 1536

# Local embedding config (sentence-transformers)
LOCAL_EMBEDDING_MODEL = "keepitreal/vietnamese-sbert"
LOCAL_EMBEDDING_DIM = 768

# Auth
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))

# Multi-LLM Engine
#   LLM_ENGINE = "openai"  → API OpenAI (gpt-4.1-mini, trả phí)
#   LLM_ENGINE = "local"   → Ollama localhost (qwen2.5:1.5b, miễn phí)
LLM_ENGINE = os.getenv("LLM_ENGINE", "openai")

# OpenAI chat model
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")

# Ollama base URL
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
# Ollama chat model
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:1.5b")

# Top K — số tài liệu cuối cùng đưa vào context cho LLM
TOP_K = int(os.getenv("TOP_K", 10))

# Upgrade dataset model
UPGRADE_DATASET_MODEL = os.getenv("UPGRADE_DATASET_MODEL", "gpt-4o-mini")

# Log file path
# Trên VPS có thể set LOG_FILE=/www/wwwlogs/python/dental-api/chat.log trong .env
LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "chat.log"))