import logging

from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .core.config import settings
from .routers.backups import router as backup_router
from .routers.instances import router as instances_router, ws_router as instances_ws_router
from .routers.schedules import router as schedule_router
from .routers.auth import router as auth_router


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application."""
    app = FastAPI(
        title="MCDock Control Panel",
        description="Manage Docker-based Minecraft servers via REST + WebSockets",
        version="0.1.0",
    )

    # Rate Limiter
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["30/minute"],
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Job Scheduler
    scheduler = AsyncIOScheduler({
        'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
    })
    scheduler.start()
    app.state.scheduler = scheduler

    # CORS
    origins = [str(o).rstrip("/") for o in settings.CORS_ORIGINS]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    api_router = APIRouter(prefix="/api")

    # Health check endpoint
    @api_router.get("/health")
    async def health():
        return {"status": "ok"}

    api_router.include_router(auth_router, tags=["auth"])
    api_router.include_router(backup_router , tags=["backups"])
    api_router.include_router(instances_router, tags=["instances"])
    api_router.include_router(instances_ws_router, tags=["ws_instances"])
    api_router.include_router(schedule_router , tags=["schedules"])
    app.include_router(api_router)

    return app


# Application entrypoint
app = create_app()
