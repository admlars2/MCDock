import tarfile
import time
from datetime import datetime, UTC
from pathlib import Path, PurePosixPath

from ..core.config import settings
from ..core.models import InstanceStatus
from .docker_service import DockerService

class BackupService:
    """
    Service for managing backups entirely in Python—no external scripts.
    """

    root = Path(settings.MC_ROOT)
    backups_root = root / "backups"
    triggered_dirname = "triggered"
    restored_dirname = "OLD_restored"

    @classmethod
    def _get_backup_dir(cls, instance_name: str, bucket: str) -> Path:
        """
        bucket = 'triggered', '5m', '1h', or any cron tag
        """
        inst_root = cls.backups_root / instance_name / bucket
        inst_root.mkdir(parents=True, exist_ok=True)
        return inst_root

    @classmethod
    def list_backups(cls, instance_name: str) -> list[str]:
        root = cls.backups_root / instance_name
        if not root.exists():
            return []
        return sorted(
            p.relative_to(root).as_posix()
            for p in root.rglob("*.tar.gz")
        )[::-1]

    @classmethod
    def trigger_backup(cls, instance_name: str, bucket: str = triggered_dirname) -> None:
        """
        bucket = 'triggered' | '5m' | '1h' | ...
        """
        inst_dir   = DockerService.get_instance_dir(instance_name)
        data_dir   = inst_dir / "data"
        backup_dir = cls._get_backup_dir(instance_name, bucket)
        status     = DockerService.get_status(instance_name)

        if status == InstanceStatus.RUNNING:
            # 1) Pause and flush saves
            DockerService.send_command(instance_name, "save-off")
            DockerService.send_command(instance_name, "save-all")
            time.sleep(3)  # wait for disk I/O

        # 2) Create the archive
        ts   = datetime.now(UTC).strftime("%Y-%m-%d-%H-%M")
        name = f"{bucket}-{ts}.tar.gz" if bucket != cls.triggered_dirname and bucket != cls.restored_dirname else f"{ts}.tar.gz"
        with tarfile.open(backup_dir / name, "w:gz") as tar:
            tar.add(data_dir, arcname="data")

        if status == InstanceStatus.RUNNING:
            # 3) Resume saves
            DockerService.send_command(instance_name, "save-on")

        # 4) Prune old backups
        max_keep = settings.BACKUP_RETENTION
        stale = sorted(backup_dir.glob("*.tar.gz"), reverse=True)[max_keep:]
        for old in stale:
            old.unlink(missing_ok=True)

    @classmethod
    def restore_backup(cls, instance: str, rel_path: str) -> None:
        """
        *rel_path* **must** be one of the strings returned by
        `list_backups`, e.g. '5m/2025-07-02-23-45.tar.gz'.
        """

        # ── sanity-check path traversal ­­­­­­­­­­­­­­­­­­­­­­­­­­­
        # keep it POSIX so the check works on every OS
        rel_posix = PurePosixPath(rel_path)
        if rel_posix.is_absolute() or ".." in rel_posix.parts:
            raise ValueError("Invalid backup path")

        archive = (cls.backups_root / instance / rel_posix).resolve()
        root    = (cls.backups_root / instance).resolve()
        if root not in archive.parents or not archive.is_file():
            raise FileNotFoundError(rel_path)

        # ── stop server & make **automatic safety snapshot**
        inst_dir = DockerService.get_instance_dir(instance)

        DockerService.stop(instance)
        cls.trigger_backup(instance, bucket=cls.restored_dirname)

        # ── unpack
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(path=inst_dir)         # recreates data/

        DockerService.start(instance)

    @classmethod
    def delete_backup(cls, instance: str, path: str) -> None:
        """
        path is the relative path returned by list_backups,
        e.g. 'triggered/2025-07-02-23-47.tar.gz'
        """
        file = cls.backups_root / instance / path
        if not file.exists() or not file.is_file():
            raise FileNotFoundError(path)
        file.unlink()