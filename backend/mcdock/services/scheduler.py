from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from datetime import UTC

from ..core.config import settings

JOB_DB = Path(settings.MC_ROOT) / "jobs.sqlite"

def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(
        timezone=UTC,
        jobstores={
            "default": SQLAlchemyJobStore(
                url=f"sqlite:///{JOB_DB}"
            )
        },
        misfire_grace_time=30,
        coalesce=True,
    )
    return scheduler
