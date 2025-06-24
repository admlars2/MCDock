# tests/test_schedules_router.py
from datetime import datetime, UTC
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError

# ── app modules (edit package names as needed) ─────────────────────────────────
from mcdock.routers import schedules as mod           # file that defines `router`
from mcdock.routers.schedules import router           # the APIRouter object
# ───────────────────────────────────────────────────────────────────────────────


# ╭─────────────────────────────  DUMMY SCHEDULER  ─────────────────────────────╮
class DummyJob:
    def __init__(self, job_id: str, trigger):
        self.id = job_id
        self.trigger = trigger
        self.next_run_time = datetime(2025, 1, 1, tzinfo=UTC)


class DummyScheduler:
    """
    Minimal drop-in replacement for AsyncIOScheduler that stores jobs in-memory.
    """
    def __init__(self):
        self._jobs = {}

    # required by /list
    def get_jobs(self):
        return list(self._jobs.values())

    # required by the two POST endpoints
    def add_job(self, *, func, trigger, args, id, replace_existing, max_instances):
        self._jobs[id] = DummyJob(id, trigger)

    # required by DELETE
    def remove_job(self, job_id):
        if job_id not in self._jobs:
            raise JobLookupError(job_id)
        del self._jobs[job_id]
# ╰──────────────────────────────────────────────────────────────────────────────╯


# ╭───────────────────────────────  TEST APP  ──────────────────────────────────╮
@pytest.fixture()
def client(monkeypatch):
    """
    Build a throw-away FastAPI app for each test, overriding:
      • auth dependency (require_token)
      • scheduler (state.scheduler)
      • DockerService / BackupService behaviour
    """
    app = FastAPI()
    app.include_router(router)

    # override token requirement
    app.dependency_overrides[mod.require_token] = lambda: None

    # attach dummy scheduler
    dummy_sched = DummyScheduler()
    app.state.scheduler = dummy_sched

    # generic patches (per-test overrides may change them)
    monkeypatch.setattr(mod.DockerService, "get_instance_dir", lambda name: Path("/dummy"))
    monkeypatch.setattr(mod.BackupService, "trigger_backup", lambda name: None)
    monkeypatch.setattr(mod.DockerService, "restart", lambda name: None)

    with TestClient(app) as c:
        # expose scheduler for assertions:  c.app.state.scheduler
        yield c
# ╰──────────────────────────────────────────────────────────────────────────────╯


# ───────────────────────────────  UNIT TESTS  ──────────────────────────────────
def test_schedule_backup_happy_path(client):
    r = client.post("/schedules/backup/alpha", json={"cron": "0 3 * * *"})
    assert r.status_code == 201
    assert r.json()["message"].startswith("Recurring backup scheduled")
    # job should be present in dummy scheduler
    assert "cron_backup_alpha" in client.app.state.scheduler._jobs


def test_schedule_restart_happy_path(client):
    r = client.post("/schedules/restart/alpha", json={"cron": "15 4 * * *"})
    assert r.status_code == 201
    assert "cron_restart_alpha" in client.app.state.scheduler._jobs


def test_invalid_cron_returns_400(client):
    r = client.post("/schedules/backup/alpha", json={"cron": "not a cron"})
    assert r.status_code == 400


def test_unknown_instance_returns_404(client, monkeypatch):
    # make DockerService raise FileNotFoundError
    monkeypatch.setattr(
        mod.DockerService, "get_instance_dir", lambda name: (_ for _ in ()).throw(FileNotFoundError)
    )
    r = client.post("/schedules/backup/missing", json={"cron": "0 5 * * *"})
    assert r.status_code == 404


def test_delete_schedule_success(client):
    # first create a job
    client.post("/schedules/restart/alpha", json={"cron": "0 6 * * *"})
    assert "cron_restart_alpha" in client.app.state.scheduler._jobs

    # now delete it
    r = client.delete("/schedules/cron_restart_alpha")
    assert r.status_code == 204
    assert "cron_restart_alpha" not in client.app.state.scheduler._jobs


def test_delete_schedule_not_found(client):
    r = client.delete("/schedules/does_not_exist")
    assert r.status_code == 404


def test_list_schedules_returns_expected(client):
    # add two jobs manually to dummy scheduler
    sched = client.app.state.scheduler
    trigger1 = CronTrigger.from_crontab("0 7 * * *")
    sched.add_job(func=lambda: None, trigger=trigger1, args=[], id="job1", replace_existing=True, max_instances=1)

    trigger2 = CronTrigger.from_crontab("30 7 * * *")
    sched.add_job(func=lambda: None, trigger=trigger2, args=[], id="job2", replace_existing=True, max_instances=1)

    r = client.get("/schedules/list")
    assert r.status_code == 200
    data = r.json()
    # ensure each job is represented once and ids match
    ids = {job["id"] for job in data}
    assert {"job1", "job2"} <= ids
