import logging

from hashlib import blake2s
from datetime import UTC
from fastapi import APIRouter, HTTPException, Request, Security
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError
from apscheduler.job import Job

from .models import ResponseMessage, CronSchedule, ScheduledJob
from ..services.backup_service import BackupService
from ..services.docker_service import DockerService
from .security import require_user, UNAUTHORIZED

router = APIRouter(
    prefix="/schedules",
    dependencies=[Security(require_user)],
    responses=UNAUTHORIZED,
)

logger = logging.getLogger(__name__)


def _validate_instance(name: str) -> None:
    try:
        DockerService.get_instance_dir(name)
    except FileNotFoundError:
        raise HTTPException(404, f"No such instance: {name}")

def _hash_tag(txt: str) -> str:
    return "h_" + blake2s(txt.encode(), digest_size=4).hexdigest()

def _cron_to_bucket(cron_spec: str) -> str:
    """
    Heuristic → turn a cron spec into a folder-friendly tag.

    ─  */5 * * * *      →  5m
    ─  0 * * * *        →  1h
    ─  0 2 * * *        →  daily-0200
    ─  complicated cron →  h_<8-char-hash>
    """
    fields = cron_spec.split()
    if len(fields) != 5:
        return _hash_tag(cron_spec)

    minute, hour, dom, month, dow = fields

    # every N minutes
    if minute.startswith("*/") and hour == "*" and dom == month == dow == "*":
        return f"{minute[2:]}m"

    # every N hours
    if hour.startswith("*/") and minute == "0" and dom == month == dow == "*":
        return f"{hour[2:]}h"

    # once a day at fixed hh:mm
    if dom == month == dow == "*":
        if minute.isdigit() and hour.isdigit():
            return f"daily-{int(hour):02d}{int(minute):02d}"

    return _hash_tag(cron_spec)

def _cron_from_trigger(trigger: CronTrigger) -> str:
    try:
        options = [str(f) for f in trigger.fields if not f.is_default]
        return " ".join(reversed(options))
    except:
        return str(trigger)

@router.get("/{instance}", response_model=list[ScheduledJob])
async def list_instance_schedules(instance: str, request: Request):
    sched: AsyncIOScheduler = request.app.state.scheduler

    all_jobs: list[Job] = sched.get_jobs()

    jobs = [
        j for j in all_jobs
        if j.id.startswith(f"cron_backup_{instance}")
        or j.id.startswith(f"cron_restart_{instance}")
    ]

    return [
        ScheduledJob(
            id=job.id,
            schedule=_cron_from_trigger(job.trigger),
            next_run=(job.next_run_time.isoformat()
                      if job.next_run_time else None),
        )
        for job in jobs
    ]


@router.post(
    "/backup/{instance}",
    status_code=201,
    response_model=ResponseMessage,
)
async def schedule_recurring_backup(
    instance: str,
    body: CronSchedule,
    request: Request,
):
    """
    Schedule a recurring backup; the *bucket* (sub-folder) is generated
    automatically from the cron spec so multiple schedules can coexist.
    """
    _validate_instance(instance)

    # 1) validate & parse cron
    try:
        trigger = CronTrigger.from_crontab(body.cron)
    except ValueError as e:
        raise HTTPException(400, f"Invalid cron expression: {e}")

    bucket = _cron_to_bucket(body.cron)
    if bucket == BackupService.triggered_dirname:
        # extremely unlikely but guard anyway
        bucket = _hash_tag(body.cron)

    # 2) register (or replace) the APScheduler job
    sched: AsyncIOScheduler = request.app.state.scheduler
    job_id = f"cron_backup_{instance}_{bucket}"

    sched.add_job(
        BackupService.trigger_backup,
        trigger=trigger,
        args=[instance, bucket],
        id=job_id,
        replace_existing=True,
        max_instances=1
    )

    # 3) respond
    return ResponseMessage(
        message=(
            f"Recurring backup scheduled for '{instance}' "
            f"({bucket}, job-id='{job_id}')."
        )
    )


@router.post(
    "/restart/{instance}",
    status_code=201,
    response_model=ResponseMessage,
)
async def schedule_recurring_restart(
    instance: str,
    body: CronSchedule,
    request: Request,
):
    _validate_instance(instance)

    try:
        trigger = CronTrigger.from_crontab(body.cron)
    except ValueError as e:
        raise HTTPException(400, f"Invalid cron expression: {e}")

    sched: AsyncIOScheduler = request.app.state.scheduler
    job_id = f"cron_restart_{instance}"

    sched.add_job(
        DockerService.restart,
        trigger=trigger,
        args=[instance],
        id=job_id,
        replace_existing=True,
        max_instances=1
    )
    return ResponseMessage(
        message=f"Recurring restart scheduled for '{instance}' as job '{job_id}'."
    )


@router.delete("/{job_id}", status_code=204)
async def delete_schedule(job_id: str, request: Request):
    sched: AsyncIOScheduler = request.app.state.scheduler
    try:
        sched.remove_job(job_id)
    except JobLookupError:
        raise HTTPException(404, f"No such schedule: {job_id}")