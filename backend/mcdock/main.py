import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from .core import logging_config  # noqa: F401 – side-effect import
from .core.config import settings
from .routers.backups   import router as backup_router
from .routers.instances import router as instances_router, ws_router as instances_ws_router
from .routers.schedules import router as schedule_router
from .routers.auth      import router as auth_router
from .services.scheduler import build_scheduler

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Build the FastAPI application with CORS, rate-limiting, routers,
    static SPA bundle, and an APScheduler that starts/stops with app life-cycle.
    """

    # ── Scheduler (created now, started in lifespan) ──────────
    scheduler = build_scheduler()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # ── startup ───────────────────────────────────────────
        scheduler.start()
        logger.info(
            "APScheduler started with %d jobs",
            len(scheduler.get_jobs(jobstore="default")),
        )
        try:
            yield
        finally:
            # ── shutdown ──────────────────────────────────────
            scheduler.shutdown(wait=False)
            logger.info("APScheduler shut down")

    app = FastAPI(
        title="MCDock Control Panel",
        description="Manage Docker-based Minecraft servers via REST + WebSockets",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Make scheduler accessible to routes / deps
    app.state.scheduler = scheduler

    # ── 5xx logger -----------------------------------------------------------
    async def log_http_5xx(request: Request, exc: StarletteHTTPException):
        if exc.status_code >= 500:
            logger.error(
                "HTTP %s on %s %s – %s",
                exc.status_code, request.method, request.url.path, exc.detail,
                exc_info=True,
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": "Internal server error"},
            )
        
        if exc.status_code == 404 and not request.url.path.startswith("/api/"):
            return FileResponse(static_path / "index.html")

        # pass-through 4xx
        return JSONResponse(status_code=exc.status_code,
                            content={"detail": exc.detail})

    app.add_exception_handler(StarletteHTTPException, log_http_5xx)

    # ── Rate limiter ---------------------------------------------------------
    limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # ── CORS -----------------------------------------------------------------
    origins = [str(o).rstrip("/") for o in settings.CORS_ORIGINS]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers --------------------------------------------------------------
    api = APIRouter(prefix="/api")

    @api.get("/health")
    async def health():
        return {"status": "ok"}

    api.include_router(auth_router,            tags=["auth"])
    api.include_router(backup_router,          tags=["backups"])
    api.include_router(instances_router,       tags=["instances"])
    api.include_router(instances_ws_router,    tags=["ws_instances"])
    api.include_router(schedule_router,        tags=["schedules"])
    app.include_router(api)

    # ── Static React bundle --------------------------------------------------
    static_path = Path(__file__).parent / "static"
    static_path.mkdir(exist_ok=True)
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")

    return app


# ASGI entry-point for Gunicorn / Uvicorn-worker
app = create_app()