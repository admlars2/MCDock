from datetime import UTC
from fastapi import (
    APIRouter, HTTPException,
    Request, Depends 
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError

from .models import ResponseMessage, CronSchedule, ScheduledJob
from ..services.docker_service import DockerService
from ..services.backup_service import BackupService
from .security import require_token


router = APIRouter(prefix="/schedules", dependencies=[Depends(require_token)])


@router.get("/list", response_model=list[ScheduledJob])
async def list_schedules(request: Request):
    
    sched: AsyncIOScheduler = request.app.state.scheduler
    jobs = sched.get_jobs()
    out: list[ScheduledJob] = []
    
    for job in jobs:
        trig = job.trigger
        # If it’s a CronTrigger created via from_crontab, it keeps the original string
        if isinstance(trig, CronTrigger) and getattr(trig, "cron_expression", None):
            spec = trig.cron_expression
        else:
            # fallback to a human-readable repr
            spec = str(trig)
        out.append(
            ScheduledJob(
                id=job.id,
                schedule=spec,
                next_run=(job.next_run_time.astimezone(UTC).isoformat() if job.next_run_time else None)
            )
        )
    return out


@router.post(
    "/backup/{instance_name}",
    status_code=201,
    response_model=ResponseMessage
)
async def schedule_recurring_backup(
    instance_name: str,
    body: CronSchedule,
    request: Request
):
    # validate instance
    try:
        BackupService.get_instance_dir(instance_name)
    except FileNotFoundError:
        raise HTTPException(404, f"No such instance: {instance_name}")

    # parse cron
    try:
        trigger = CronTrigger.from_crontab(body.cron)
    except ValueError as e:
        raise HTTPException(400, f"Invalid cron expression: {e}")

    sched: AsyncIOScheduler = request.app.state.scheduler
    job_id = f"cron_backup_{instance_name}"
    sched.add_job(
        func=BackupService.trigger_backup,
        trigger=trigger,
        args=[instance_name],
        id=job_id,
        replace_existing=True,
        max_instances=1,
    )
    return ResponseMessage(message=f"Recurring backup scheduled for '{instance_name}' as job '{job_id}'")


@router.post(
    "/restart/{instance_name}",
    status_code=201,
    response_model=ResponseMessage
)
async def schedule_recurring_restart(
    instance_name: str,
    body: CronSchedule,
    request: Request
):
    # validate instance
    try:
        BackupService.get_instance_dir(instance_name)
    except FileNotFoundError:
        raise HTTPException(404, f"No such instance: {instance_name}")

    # parse cron
    try:
        trigger = CronTrigger.from_crontab(body.cron)
    except ValueError as e:
        raise HTTPException(400, f"Invalid cron expression: {e}")

    sched: AsyncIOScheduler = request.app.state.scheduler
    job_id = f"cron_restart_{instance_name}"
    sched.add_job(
        func=DockerService.restart,
        trigger=trigger,
        args=[instance_name],
        id=job_id,
        replace_existing=True,
        max_instances=1,
    )
    return ResponseMessage(message=f"Recurring restart scheduled for '{instance_name}' as job '{job_id}'")


@router.delete("/{job_id}", status_code=204)
async def delete_schedule(job_id: str, request: Request):
    try:
        sched: AsyncIOScheduler = request.app.state.scheduler
        sched.remove_job(job_id)
    except JobLookupError:
        raise HTTPException(404, f"No such schedule: {job_id}")