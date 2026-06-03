import os
import time
import logging
import platform

from fastapi import APIRouter

from src.database.database import engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

_start_time = time.time()


@router.get("/health/detail")
def health_detail():
    """
    Endpoint chi tiết để monitoring trạng thái app.
    Trả về: DB pool status, uptime, memory usage, system info.
    """
    # DB Pool info
    pool = engine.pool
    pool_info = {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool._invalidate_time if hasattr(pool, "_invalidate_time") else None,
    }

    # Uptime
    uptime_seconds = time.time() - _start_time
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    uptime_str = f"{hours}h {minutes}m"

    # Memory (nếu psutil khả dụng)
    memory_info = {}
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem = process.memory_info()
        memory_info = {
            "rss_mb": round(mem.rss / 1024 / 1024, 1),
            "vms_mb": round(mem.vms / 1024 / 1024, 1),
        }
    except ImportError:
        memory_info = {"note": "psutil không khả dụng"}
    except Exception as e:
        memory_info = {"error": str(e)}

    # Kết quả
    result = {
        "status": "ok",
        "uptime": uptime_str,
        "uptime_seconds": round(uptime_seconds),
        "pid": os.getpid(),
        "python": platform.python_version(),
        "db_pool": pool_info,
        "memory": memory_info,
    }

    # Cảnh báo nếu pool gần cạn
    used = pool_info["checked_out"]
    total = pool_info["pool_size"] + max(pool.overflow(), 0)
    if total > 0 and used / total > 0.8:
        result["warning"] = f"DB pool sắp cạn: {used}/{total} connections đang dùng"
        logger.warning("[HEALTH] %s", result["warning"])

    return result
