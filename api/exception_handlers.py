import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, SQLAlchemyError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI):
    """Đăng ký các exception handler cho app."""

    @app.exception_handler(OperationalError)
    async def db_operational_error_handler(request: Request, exc: OperationalError):
        logger.error("Lỗi kết nối database: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"detail": "Hệ thống đang gặp sự cố kết nối database. Vui lòng thử lại sau."},
        )

    @app.exception_handler(SQLAlchemyError)
    async def db_generic_error_handler(request: Request, exc: SQLAlchemyError):
        logger.error("Lỗi database: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"detail": "Lỗi database. Vui lòng thử lại sau."},
        )
