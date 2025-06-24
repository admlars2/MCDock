import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from .core.config import settings
from .routers.instances import router as instances_router


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

    # CORS (adjust origins as needed)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(instances_router, prefix="/instances", tags=["instances"])

    # Health check endpoint
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.middleware("http")
    async def log_requests(request, call_next):
        logger.info(f"→ {request.method} {request.url.path}")
        resp = await call_next(request)
        logger.info(f"← {resp.status_code} {request.url.path}")
        return resp

    return app


# Application entrypoint
app = create_app()
