# project directory
chdir = '/www/wwwroot/dental-api'

# worker processes
workers = 2

# threads per worker
threads = 2

# user to run as
user = 'www'

# worker type
worker_class = 'uvicorn.workers.UvicornWorker'

# bind IP and port
bind = '0.0.0.0:8000'

# PID file path (used for stopping and restarting; do not remove)
pidfile = '/www/wwwroot/dental-api/gunicorn.pid'

# access log and error log paths, file name do not change 'gunicorn_acess.log', 'gunicorn_error.log'
accesslog = '/www/wwwlogs/python/dental-api/gunicorn_acess.log'
errorlog = '/www/wwwlogs/python/dental-api/gunicorn_error.log'

# Log level (this log level applies to the error log; the access log level cannot be configured)
# debug: Debug level;
# info: Normal level;
# warning: Warning messages level;
# error: Error level;
# critical: Critical errors;
loglevel = 'info'

# Put custom settings here
# It is best to follow the same format as above: <comment + newline + key = value>.
# PS: Gunicorn configuration files are Python\-style (i.e., ".py" files); make sure to follow Python syntax.
# For example: if a config value (such as loglevel) is a string, it must be enclosed in quotes.

# worker timeout (seconds)
timeout = 600

# graceful shutdown timeout (seconds)
graceful_timeout = 30

# HTTP keep-alive timeout (seconds)
keepalive = 120

# auto-restart worker
max_requests = 500
max_requests_jitter = 100


# Chạy sau khi Gunicorn fork mỗi worker process.
# Mỗi worker có HTTP connection pool riêng nên cần warm-up độc lập.
def post_fork(server, worker):
    import asyncio
    import logging
    import os
    import sys

    sys.path.insert(0, chdir)
    os.chdir(chdir)

    log = logging.getLogger("gunicorn.error")

    async def _warmup():
        try:
            from openai import AsyncOpenAI
            from src.config import LLM_ENGINE, OPENAI_API_KEY, OPENAI_CHAT_MODEL

            if LLM_ENGINE != "openai":
                return

            client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            t0 = asyncio.get_event_loop().time()
            await client.chat.completions.create(
                model=OPENAI_CHAT_MODEL,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
                temperature=0,
            )
            await client.close()
            elapsed = asyncio.get_event_loop().time() - t0
            log.info("[WORKER %s] LLM warm-up xong trong %.2fs", worker.pid, elapsed)
        except Exception as exc:
            log.warning("[WORKER %s] LLM warm-up thất bại (bỏ qua): %s", worker.pid, exc)

    asyncio.run(_warmup())
