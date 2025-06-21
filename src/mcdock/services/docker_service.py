import subprocess
from pathlib import Path

from ..config import settings


class DockerService:
    """
    Service for managing Docker-compose based Minecraft instances.
    """
    root = Path(settings.MC_ROOT)

    @classmethod
    def _get_instance_dir(cls, instance_name: str) -> Path:
        path = cls.root / instance_name
        if not path.exists() or not path.is_dir():
            raise FileNotFoundError(f"Instance not found: {instance_name}")
        return path

    @classmethod
    def get_status(cls, instance_name: str) -> str:
        """
        Returns 'running' if any container is up, 'stopped' otherwise.
        """
        path = cls._get_instance_dir(instance_name)
        try:
            # List containers for this compose project
            result = subprocess.run(
                ["docker", "compose", "ps", "-q"],
                cwd=path,
                capture_output=True,
                text=True,
                check=True
            )
            # If any container ID is shown, it's running
            if result.stdout.strip():
                return "running"
            return "stopped"
        except subprocess.CalledProcessError:
            return "error"

    @classmethod
    def start(self, instance_name: str) -> None:
        """
        Starts the Docker-compose project (detached).
        """
        path = self._get_instance_dir(instance_name)
        subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=path,
            check=True
        )

    @classmethod
    def stop(self, instance_name: str) -> None:
        """
        Stops the Docker-compose project and removes containers.
        """
        path = self._get_instance_dir(instance_name)
        subprocess.run(
            ["docker", "compose", "down"],
            cwd=path,
            check=True
        )

    @classmethod
    def stream_logs(self, instance_name: str) -> subprocess.Popen:
        return subprocess.Popen(
            ["docker", "logs", "-f", instance_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
    
    @classmethod
    def stream_stats(self, instance_name: str) -> subprocess.Popen:
        """
        Return a subprocess that streams live Docker stats for the given instance.
        """
        path = self._get_instance_dir(instance_name)
        result = subprocess.run(
            ["docker", "compose", "ps", "-q"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        container_ids = result.stdout.strip().splitlines()
        if not container_ids:
            raise RuntimeError(f"No running containers for instance: {instance_name}")
        # Stream stats for the first container
        return subprocess.Popen(
            ["docker", "stats", container_ids[0], "--no-stream"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )