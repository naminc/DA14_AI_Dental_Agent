import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from src.database.database import engine
from src.chat.dependencies import get_chatbot

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi động: kiểm tra kết nối DB
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("[STARTUP] Kết nối database OK")
    except Exception as e:
        logger.error("[STARTUP] Kết nối database THẤT BẠI: %s", e)

    logger.info("[STARTUP] Đang khởi tạo DentalChatbot + load Embedding model...")
    get_chatbot()
    logger.info("[STARTUP] Sẵn sàng nhận request.")
    yield

    # Shutdown: giải phóng toàn bộ connection pool
    engine.dispose()
    logger.info("[SHUTDOWN] Đã giải phóng connection pool")
