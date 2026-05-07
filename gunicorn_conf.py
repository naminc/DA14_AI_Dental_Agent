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
timeout = 300

# graceful shutdown timeout (seconds)
graceful_timeout = 30

# HTTP keep-alive timeout (seconds)
keepalive = 75

# auto-restart worker
max_requests = 1000
max_requests_jitter = 100
