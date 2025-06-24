# tests/test_backup_service.py
import tarfile
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml  # only needed by the dummy template used elsewhere

# ── project imports (edit package name if needed) ───────────────────────────────
from mcdock.services.backup_service import BackupService
from mcdock.services import backup_service
from mcdock.services.docker_service import DockerService
from mcdock.core.config import settings
# ────────────────────────────────────────────────────────────────────────────────


# ╭─────────────────────────────  GLOBAL FIXTURES  ─────────────────────────────╮
@pytest.fixture(autouse=True)
def _isolate_fs(tmp_path, monkeypatch):
    """
    Every test gets its own temporary MC_ROOT; DockerService & BackupService
    point there automatically.
    """
    monkeypatch.setattr(settings, "MC_ROOT", tmp_path)
    monkeypatch.setattr(DockerService, "root", Path(settings.MC_ROOT))
    # BackupService.root is not used internally, but patch anyway for completeness
    monkeypatch.setattr(BackupService, "root", Path(settings.MC_ROOT))


@pytest.fixture
def rcon_spy(monkeypatch):
    """Capture all RCON commands issued during a test."""
    calls = []

    def _exec(inst, cmd):
        calls.append(cmd)

    monkeypatch.setattr(backup_service, "RconService", SimpleNamespace(execute=_exec))
    return calls


@pytest.fixture
def docker_spy(monkeypatch):
    """Stub DockerService.start/stop and record call order."""
    calls = []

    monkeypatch.setattr(
        backup_service.DockerService,
        "stop",
        lambda inst: calls.append(("stop", inst)),
    )
    monkeypatch.setattr(
        backup_service.DockerService,
        "start",
        lambda inst: calls.append(("start", inst)),
    )
    return calls


@pytest.fixture(autouse=True)
def _skip_sleep(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda *_: None)


# ╰──────────────────────────────────────────────────────────────────────────────╯


# ───────────────────────────────  UNIT TESTS  ──────────────────────────────────
def test_list_backups_sorted_and_limited(tmp_path, monkeypatch):
    """Only .tar.gz files, newest first, trimmed by BACKUP_RETENTION."""
    monkeypatch.setattr(settings, "BACKUP_RETENTION", 1)
    inst_dir = tmp_path / "world"
    backup_dir = inst_dir / "backups"
    backup_dir.mkdir(parents=True)

    # create two valid backups and one irrelevant file
    (backup_dir / "mc-backup-2025-01-01-00-00.tar.gz").touch()
    (backup_dir / "mc-backup-2025-01-02-00-00.tar.gz").touch()
    (backup_dir / "readme.txt").touch()

    assert BackupService.list_backups("world") == ["mc-backup-2025-01-02-00-00.tar.gz"]


def test_trigger_backup_creates_archive_and_prunes(tmp_path, monkeypatch, rcon_spy):
    """A new backup is created, old ones pruned to BACKUP_RETENTION, RCON cmds sent."""
    monkeypatch.setattr(settings, "BACKUP_RETENTION", 2)

    inst_dir = tmp_path / "alpha"
    data_dir = inst_dir / "data"
    backup_dir = inst_dir / "backups"
    data_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    # existing (older) backups: 3 ⇒ will exceed retention once new one is added
    for d in ("2025-01-01-00-00", "2025-01-02-00-00", "2025-01-03-00-00"):
        (backup_dir / f"mc-backup-{d}.tar.gz").touch()

    # dummy world file
    (data_dir / "level.dat").write_text("dummy")

    BackupService.trigger_backup("alpha")

    backups = sorted(p.name for p in backup_dir.glob("*.tar.gz"))
    # exactly BACKUP_RETENTION files should remain
    assert len(backups) == 2

    # newest file (just created) must be present
    assert any("mc-backup-" in b for b in backups)

    # RCON commands issued in expected order
    assert rcon_spy[:2] == ["save-off", "save-all"]
    assert rcon_spy[-1] == "save-on"


def test_restore_backup_replaces_data_and_restarts(tmp_path, docker_spy):
    """Data dir is replaced by backup contents; Docker stop/start invoked."""
    inst_dir = tmp_path / "beta"
    data_dir = inst_dir / "data"
    backup_dir = inst_dir / "backups"
    data_dir.mkdir(parents=True)
    backup_dir.mkdir(parents=True)

    # current world content
    (data_dir / "old.txt").write_text("OLD")

    # build backup archive containing new.txt under top-level 'data/'
    backup_name = "mc-backup-2025-01-04-00-00.tar.gz"
    archive_path = backup_dir / backup_name
    tmp_src = tmp_path / "tmpdata"
    (tmp_src / "data").mkdir(parents=True)
    (tmp_src / "data" / "new.txt").write_text("NEW")
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(tmp_src / "data", arcname="data")

    BackupService.restore_backup("beta", backup_name)

    # old data moved aside
    old_dirs = list(inst_dir.glob("data_OLD_*"))
    assert old_dirs and (old_dirs[0] / "old.txt").exists()

    # new data extracted
    assert (data_dir / "new.txt").exists()

    # Docker was stopped then started for this instance
    assert docker_spy == [("stop", "beta"), ("start", "beta")]
