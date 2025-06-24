import uuid

from datetime import datetime, UTC
from fastapi import (
    APIRouter, HTTPException, 
    Request, Depends
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from .models import ResponseMessage
from ..services.backup_service import BackupService
from ..services.docker_service import DockerService
from .security import require_token


router = APIRouter(prefix="/backups", dependencies=[Depends(require_token)])


@router.get("/{instance_name}", response_model=list[str])
async def list_backups(instance_name: str):
    """
    List the last BACKUP_RETENTION backups for an instance.
    """
    try:
        files = BackupService.list_backups(instance_name=instance_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return files


@router.post("/{instance_name}/trigger", status_code=202, response_model=ResponseMessage)
async def trigger_backup(
    instance_name: str,
    request: Request
):
    # 1) validate the instance exists (your existing helper)
    try:
        DockerService.get_instance_dir(instance_name)
    except FileNotFoundError:
        raise HTTPException(404, f"No such instance: {instance_name}")

    # 2) schedule the actual backup method to run AFTER sending the 202

    sched: AsyncIOScheduler = request.app.state.scheduler
    job_id = f"backup_{instance_name}_{uuid.uuid4().hex}"
    sched.add_job(
        func=BackupService.trigger_backup,
        trigger=DateTrigger(run_date=datetime.now(UTC)),
        args=[instance_name],
        id=job_id,
        max_instances=1,
    )

    # 3) immediately return 202—client can poll list_backups or logs if you expose them
    return ResponseMessage(message=f"Backup for '{instance_name}' is being created.")


@router.post("/{instance_name}/{filename}/restore", status_code=202, response_model=ResponseMessage)
async def restore_backup(
    instance_name: str, 
    filename: str,
    request: Request
):
    """
    Trigger a restoration for a given instance and filename.
    """
    try:
        DockerService.get_instance_dir(instance_name)
    except FileNotFoundError:
        raise HTTPException(404, f"No such instance: {instance_name}")

    sched: AsyncIOScheduler = request.app.state.scheduler
    job_id = f"restore_{instance_name}_{filename}_{uuid.uuid4().hex}"
    sched.add_job(
        func=BackupService.restore_backup,
        trigger=DateTrigger(run_date=datetime.now(UTC)),
        args=[instance_name, filename],
        id=job_id,
        max_instances=1,
    )

    return ResponseMessage(message=f"Restoring '{filename}' for '{instance_name}' in background.")