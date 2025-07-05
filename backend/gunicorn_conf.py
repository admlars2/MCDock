bind = "0.0.0.0:8000"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
graceful_timeout = 30
timeout = 60
keepalive = 2
loglevel = "info"