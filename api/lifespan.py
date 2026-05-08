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
from src.config import LOG_FILE

logger = logging.getLogger(__name__)

_FORMATTER = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

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

    yield

    try:
        engine.dispose()
        logger.info("[SHUTDOWN] Đã giải phóng connection pool")
    except Exception as e:
        logger.warning("[SHUTDOWN] Lỗi khi dispose engine: %s", e)
