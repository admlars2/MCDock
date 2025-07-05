import logging
from logging.handlers import (
    RotatingFileHandler,
    QueueHandler,
    QueueListener,
)
from pathlib import Path
from queue import SimpleQueue

from .config import settings

# ───────── setup ─────────────────────────────────────────────────
LOG_LEVEL = logging.INFO
LOG_FMT   = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FMT  = "%Y-%m-%d %H:%M:%S"
fmt       = logging.Formatter(LOG_FMT, DATE_FMT)

# ───────── fallback-safe log targets ─────────────────────────────
console = logging.StreamHandler()
console.setFormatter(fmt)
console.setLevel(LOG_LEVEL)

handlers = [console]

# ───────── try rotating file logger (safe fallback if no perms) ─
try:
    LOG_DIR = Path(settings.MC_ROOT) / "mcdock-logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE = LOG_DIR / "mcdock.log"

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=2 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(LOG_LEVEL)
    handlers.append(file_handler)

except Exception as e:
    logging.basicConfig(level=logging.WARNING)
    logging.warning(f"[logging] Could not set up file logging: {e}")

# ───────── queue + listener ──────────────────────────────────────
log_queue = SimpleQueue()
queue_handler = QueueHandler(log_queue)
listener = QueueListener(log_queue, *handlers, respect_handler_level=True)
listener.daemon = True
listener.start()

# ───────── root logger ───────────────────────────────────────────
logging.basicConfig(
    level=LOG_LEVEL,
    handlers=[queue_handler],
    force=True,
)

# ───────── third-party noise filter ──────────────────────────────
logging.getLogger("urllib3").setLevel(logging.WARNING)