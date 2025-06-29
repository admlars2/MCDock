import logging

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from .core.config import settings
from .routers.backups import router as backup_router
from .routers.instances import router as instances_router
from .routers.schedules import router as schedule_router


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application."""
    app = FastAPI(
        title="MCDock Control Panel",
        description="Manage Docker-based Minecraft servers via REST + WebSockets",
        version="0.1.0",
    )

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

    api_router.include_router(backup_router , tags=["backups"])
    api_router.include_router(instances_router, tags=["instances"])
    api_router.include_router(schedule_router , tags=["schedules"])
    app.include_router(api_router)

    @app.middleware("http")
    async def log_requests(request, call_next):
        logger.info(f"→ {request.method} {request.url.path}")
        resp = await call_next(request)
        logger.info(f"← {resp.status_code} {request.url.path}")
        return resp

    return app


# Application entrypoint
app = create_app()
