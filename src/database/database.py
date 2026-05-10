import logging

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import OperationalError, DisconnectionError
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from src.config import DATABASE_URL

logger = logging.getLogger(__name__)

# Kiểm tra DATABASE_URL
if not DATABASE_URL:
    raise ValueError("Thiếu DATABASE_URL trong file .env")

# Tạo engine với cấu hình connection pool
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,        # Kiểm tra connection có sống không
    pool_recycle=280,          # Tái tạo connection sau 280s
    pool_size=5,               # Số connection tối đa trong pool
    max_overflow=10,           # Số connection tối đa vượt quá pool_size
    pool_timeout=30,           # Chờ tối đa 30s để lấy connection từ pool
    echo=False,
    connect_args={
        "connect_timeout": 10,  # Chờ tối đa 10s để kết nối
    },
)

# Tạo session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tạo Base cho models
Base = declarative_base()


@event.listens_for(engine, "engine_connect")
def _on_engine_connect(connection):
    logger.debug("Đã tạo connection mới")


@event.listens_for(engine, "checkout")
def _on_checkout(dbapi_connection, connection_record, connection_proxy):
    """Kiểm tra connection khi lấy ra từ pool."""
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
    except Exception:
        logger.warning("Phát hiện connection đã chết, đang tạo mới...")
        raise DisconnectionError("Connection đã hết hạn")


def get_db():
    """FastAPI dependency — cung cấp session, luôn đóng khi kết thúc request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
