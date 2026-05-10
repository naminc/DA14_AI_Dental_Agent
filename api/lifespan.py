import asyncio
import logging
import logging.handlers
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy import text

from src.database.database import engine
from src.chat.dependencies import get_chatbot
from src.config import LOG_FILE, LLM_ENGINE, OPENAI_API_KEY, OPENAI_CHAT_MODEL

logger = logging.getLogger(__name__)

# Warmup LLM connection
async def _warmup_llm_connection() -> None:
    """Pre-establish kết nối HTTP/TLS tới OpenAI để câu hỏi đầu tiên không bị chậm."""
    if LLM_ENGINE != "openai":
        return
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        t0 = asyncio.get_event_loop().time()
        await client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
            temperature=0,
        )
        await client.close()
        logger.info("[STARTUP] LLM warm-up xong trong %.2fs", asyncio.get_event_loop().time() - t0)
    except Exception as e:
        logger.warning("[STARTUP] LLM warm-up thất bại (bỏ qua): %s", e)


# Configure logging
_FORMATTER = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Configure logging
def _configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    target_log_path = str(Path(LOG_FILE))
    has_file = any(
        isinstance(h, logging.handlers.TimedRotatingFileHandler)
        and str(getattr(h, "baseFilename", "")) == target_log_path
        for h in root.handlers
    )

    if not has_file:
        try:
            log_path = Path(LOG_FILE)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.handlers.TimedRotatingFileHandler(
                filename=log_path,
                when="midnight",
                interval=1,
                backupCount=30,
                encoding="utf-8",
            )
            file_handler.setFormatter(_FORMATTER)
            root.addHandler(file_handler)
        except Exception as e:
            sys.stderr.write(f"[LOG] Không thể mở file log '{LOG_FILE}': {e}\n")

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_logging()

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("[STARTUP] Kết nối database OK")
    except Exception as e:
        logger.error("[STARTUP] Kết nối database THẤT BẠI: %s", e)

    logger.info("[STARTUP] Đang khởi tạo DentalChatbot + load Embedding model...")
    try:
        get_chatbot()
        logger.info("[STARTUP] Sẵn sàng nhận request.")
    except Exception as e:
        logger.exception("[STARTUP] Khởi tạo DentalChatbot lỗi: %s", e)

    await _warmup_llm_connection()

    yield

    try:
        engine.dispose()
        logger.info("[SHUTDOWN] Đã giải phóng connection pool")
    except Exception as e:
        logger.warning("[SHUTDOWN] Lỗi khi dispose engine: %s", e)
