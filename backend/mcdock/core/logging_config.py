import logging
from logging.handlers import (
    RotatingFileHandler,
    QueueHandler,
    QueueListener,
)
from pathlib import Path
from queue import SimpleQueue

from .config import settings

# ───────── paths ──────────────────────────────────────────────────
LOG_DIR  = Path(settings.MC_ROOT) / "mcdock-logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "mcdock.log"

# ───────── format / level ─────────────────────────────────────────
LOG_LEVEL = logging.INFO
LOG_FMT   = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FMT  = "%Y-%m-%d %H:%M:%S"
fmt       = logging.Formatter(LOG_FMT, DATE_FMT)

# ───────── real (blocking) handlers: console + rotating file ──────
console = logging.StreamHandler()
console.setFormatter(fmt)
console.setLevel(LOG_LEVEL)

file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=2 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
file_handler.setFormatter(fmt)
file_handler.setLevel(LOG_LEVEL)

# ───────── queue + listener thread ────────────────────────────────
log_queue    = SimpleQueue()
queue_handler = QueueHandler(log_queue)            # non-blocking publisher
listener      = QueueListener(
    log_queue,
    console,
    file_handler,
    respect_handler_level=True,
)
listener.daemon = True
listener.start()

# ───────── root logger config (publishes to queue) ────────────────
logging.basicConfig(
    level=LOG_LEVEL,
    handlers=[queue_handler],   # only the fast queue handler
    force=True,
)

logging.getLogger("urllib3").setLevel(logging.WARNING)