# routers/backups.py
import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, HTTPException, Request, Security
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from ..services.backup_service import BackupService
from ..services.docker_service import DockerService
from .models import ResponseMessage
from .security import require_user, UNAUTHORIZED

router = APIRouter(
    prefix="/backups",
    dependencies=[Security(require_user)],
    responses=UNAUTHORIZED,
)

# ────────────────────────────────────────────────────────────────
# helpers
# ────────────────────────────────────────────────────────────────
def _validate_instance(name: str) -> None:
    try:
        DockerService.get_instance_dir(name)
    except FileNotFoundError:
        raise HTTPException(404, f"No such instance: {name}")


@router.get("/{instance}", response_model=list[str])
async def list_backups(instance: str):
    return BackupService.list_backups(instance)


@router.put("/{instance}/trigger", status_code=202, response_model=ResponseMessage)
async def trigger_backup(instance: str, request: Request):
    _validate_instance(instance)

    sched: AsyncIOScheduler = request.app.state.scheduler
    sched.add_job(
        BackupService.trigger_backup,
        DateTrigger(run_date=datetime.now(UTC)),
        args=[instance, BackupService.triggered_dirname],
        id=f"trigger_{instance}_{uuid.uuid4().hex}",
        max_instances=1,
    )
    return ResponseMessage(message=f"Backup for '{instance}' is being created.")


@router.post(
    "/{instance}/{bucket}/{filename}/restore",
    status_code=202,
    response_model=ResponseMessage,
)
async def restore_backup(instance: str, bucket: str, filename: str, request: Request):
    _validate_instance(instance)

    sched: AsyncIOScheduler = request.app.state.scheduler
    sched.add_job(
        BackupService.restore_backup,
        DateTrigger(run_date=datetime.now(UTC)),
        args=[instance, f"{bucket}/{filename}"],
        id=f"restore_{uuid.uuid4().hex}",
        max_instances=1,
    )
    return ResponseMessage(
        message=f"Restoring '{bucket}/{filename}' for '{instance}' in background."
    )


@router.delete("/{instance}/{bucket}/{filename}", status_code=204)
async def delete_backup(instance: str, bucket: str, filename: str):
    _validate_instance(instance)
    try:
        BackupService.delete_backup(instance, f"{bucket}/{filename}")
    except FileNotFoundError:
        raise HTTPException(404, "Backup not found.")