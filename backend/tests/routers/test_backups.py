# tests/test_backups_router.py
from datetime import datetime, UTC
from pathlib import Path
from types import SimpleNamespace
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apscheduler.triggers.date import DateTrigger

# ── import router & module -----------------------------------------------------
from mcdock.routers import backups as mod          # module that defines the router
from mcdock.routers.backups import router          # APIRouter instance
# ------------------------------------------------------------------------------


# ╭───────────────────────────── Dummy scheduler ───────────────────────────────╮
class DummyJob:
    def __init__(self, job_id: str, trigger):
        self.id = job_id
        self.trigger = trigger
        self.next_run_time = datetime(2025, 1, 1, tzinfo=UTC)


class DummyScheduler:
    """Very small subset of AsyncIOScheduler used by the router."""
    def __init__(self):
        self.jobs = {}

    def add_job(self, *, func, trigger, args, id, max_instances):
        self.jobs[id] = DummyJob(id, trigger)

    def get_jobs(self):
        return list(self.jobs.values())
# ╰──────────────────────────────────────────────────────────────────────────────╯


# ╭────────────────────────── shared client fixture ────────────────────────────╮
@pytest.fixture
def client(monkeypatch):
    """Create a throw-away FastAPI app for each test run."""
    app = FastAPI()
    app.include_router(router)

    # Bypass token auth
    app.dependency_overrides[mod.require_token] = lambda: None

    # Dummy scheduler
    sched = DummyScheduler()
    app.state.scheduler = sched

    # Patch DockerService helpers (can be overridden per-test)
    monkeypatch.setattr(
        mod.DockerService,
        "get_instance_dir",
        lambda inst: Path(f"/fake/{inst}")  # accept any name by default
    )

    # Patch BackupService methods (no-op stubs; can be spied later)
    monkeypatch.setattr(mod.BackupService, "list_backups", lambda instance_name: ["a.tar.gz", "b.tar.gz"])
    monkeypatch.setattr(mod.BackupService, "trigger_backup", lambda instance_name: None)
    monkeypatch.setattr(mod.BackupService, "restore_backup", lambda instance_name, filename: None)

    with TestClient(app) as c:
        yield c
# ╰──────────────────────────────────────────────────────────────────────────────╯


# ────────────────────────────────── tests ──────────────────────────────────────
def test_list_backups_success(client):
    r = client.get("/backups/world")
    assert r.status_code == 200
    assert r.json() == ["a.tar.gz", "b.tar.gz"]


def test_list_backups_500_on_missing(monkeypatch, client):
    def _raise(_):
        raise FileNotFoundError("no dir")
    monkeypatch.setattr(mod.BackupService, "list_backups", _raise)

    r = client.get("/backups/missing")
    assert r.status_code == 500


def test_trigger_backup_schedules_job(client):
    r = client.post("/backups/world/trigger")
    assert r.status_code == 202
    # exactly one new job, id starts with 'backup_world_'
    job_ids = list(client.app.state.scheduler.jobs.keys())
    assert len(job_ids) == 1
    assert job_ids[0].startswith("backup_world_")


def test_trigger_backup_unknown_instance(monkeypatch, client):
    monkeypatch.setattr(
        mod.DockerService, "get_instance_dir", lambda inst: (_ for _ in ()).throw(FileNotFoundError)
    )
    r = client.post("/backups/ghost/trigger")
    assert r.status_code == 404


def test_restore_backup_schedules_job(client):
    r = client.post("/backups/world/save1.tar.gz/restore")
    assert r.status_code == 202
    job_ids = list(client.app.state.scheduler.jobs.keys())
    assert len(job_ids) == 1
    assert job_ids[0].startswith("restore_world_save1.tar.gz_")
    # ensure the trigger is a DateTrigger set to now (± small delta)
    job = client.app.state.scheduler.jobs[job_ids[0]]
    assert isinstance(job.trigger, DateTrigger)


def test_restore_backup_unknown_instance(monkeypatch, client):
    monkeypatch.setattr(
        mod.DockerService, "get_instance_dir", lambda inst: (_ for _ in ()).throw(FileNotFoundError)
    )
    r = client.post("/backups/ghost/save1.tar.gz/restore")
    assert r.status_code == 404
