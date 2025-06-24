import tarfile
import time
from datetime import datetime, UTC
from pathlib import Path

from ..core.config import settings
from .rcon_service import RconService
from .docker_service import DockerService


class BackupService:
    """
    Service for managing backups entirely in Python—no external scripts.
    """

    root = Path(settings.MC_ROOT)

    @classmethod
    def _get_backup_dir(cls, instance_name: str) -> Path:
        inst_dir = DockerService.get_instance_dir(instance_name)
        backup_dir = inst_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    @classmethod
    def list_backups(cls, instance_name: str) -> list[str]:
        backup_dir = cls._get_backup_dir(instance_name)
        files = [p.name for p in backup_dir.iterdir() if p.suffix == ".tar.gz"]
        files.sort(reverse=True)  # newest first by lexicographic timestamp
        return files[: settings.BACKUP_RETENTION]

    @classmethod
    def trigger_backup(cls, instance_name: str) -> None:
        inst_dir = DockerService.get_instance_dir(instance_name)
        data_dir = inst_dir / "data"
        backup_dir = cls._get_backup_dir(instance_name)

        # 1) Pause and flush saves
        RconService.execute(instance_name, "save-off")
        RconService.execute(instance_name, "save-all")
        time.sleep(3)  # wait for disk I/O

        # 2) Create the archive
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d-%H-%M")
        archive_path = backup_dir / f"mc-backup-{timestamp}.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            # add the entire data folder, but store under "data" in the archive
            tar.add(data_dir, arcname="data")

        # 3) Resume saves
        RconService.execute(instance_name, "save-on")

        # 4) Prune old backups
        all_backups = sorted(backup_dir.iterdir(), reverse=True)
        for old in all_backups[settings.BACKUP_RETENTION :]:
            try:
                old.unlink()
            except Exception:
                pass  # ignore deletion errors

    @classmethod
    def restore_backup(cls, instance_name: str, filename: str) -> None:
        """
        Restore the given backup over the instance's data directory.
        """
        inst_dir   = DockerService.get_instance_dir(instance_name)
        backup_dir = cls._get_backup_dir(instance_name)
        archive    = backup_dir / filename
        data_dir   = inst_dir / "data"

        if not archive.exists():
            raise FileNotFoundError(f"Backup not found: {filename}")

        # 1) Stop the instance
        DockerService.stop(instance_name)

        # 2) (Optionally) move current data out of the way
        old_dir = inst_dir / f"data_OLD_{filename}"
        if data_dir.exists():
            data_dir.rename(old_dir)

        # 3) Extract backup
        with tarfile.open(archive, "r:gz") as tar:
            # tar was created with arcname="data", so this will recreate data/
            tar.extractall(path=inst_dir)

        # 4) Start the instance
        DockerService.start(instance_name)