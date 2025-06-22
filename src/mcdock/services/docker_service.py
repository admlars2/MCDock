import subprocess
import shutil
from pathlib import Path

from ..config import settings


class DockerService:
    """
    Service for managing Docker-compose based Minecraft instances.
    """
    root = Path(settings.MC_ROOT)

    @classmethod
    def get_instance_dirs(cls) -> list[Path]:
        root = Path(settings.MC_ROOT)
        if not root.exists() or not root.is_dir():
            raise ValueError(f"MC_ROOT path not found: {settings.MC_ROOT}")
        return [p for p in root.iterdir() if p.is_dir()]

    @classmethod
    def get_instance_dir(cls, instance_name: str) -> Path:
        path = cls.root / instance_name
        if not path.exists() or not path.is_dir():
            raise FileNotFoundError(f"Instance not found: {instance_name}")
        return path
    
    @classmethod
    def create_instance(instance_name: str, compose: str) -> None:
        root = Path(settings.MC_ROOT)
        inst_dir = root / instance_name

        if inst_dir.exists():
            raise ValueError(f"Instance '{instance_name}' already exists.")

        # 1) create the folder
        try:
            inst_dir.mkdir(parents=True, exist_ok=False)
        except Exception as e:
            raise ValueError(f"Failed to create instance directory: {e}")

        # 2) write the user-supplied compose file
        try:
            (inst_dir / "docker-compose.yml").write_text(compose)
        except Exception as e:
            raise ValueError(500, f"Failed to write compose file: {e}")
        
    @classmethod
    def get_compose(instance_name: str) -> str:
        compose_file = Path(settings.MC_ROOT) / instance_name / "docker-compose.yml"
        if not compose_file.exists():
            raise ValueError(f"No docker-compose.yml in '{instance_name}'")

        try:
            return compose_file.read_text()
        except Exception as e:
            raise ValueError(f"Failed to read compose file: {e}")
        
    @classmethod
    def update_compose(instance_name: str, compose: str) -> None:
        root = Path(settings.MC_ROOT)
        inst_dir = root / instance_name
        
        if not inst_dir.exists() or not inst_dir.is_dir():
            raise ValueError(404, f"No such instance: {instance_name}")
        
        compose_file = inst_dir / "docker-compose.yml"
        if not compose_file.exists():
            raise ValueError(404, f"No docker-compose.yml in '{instance_name}'")

        try:
            compose_file.write_text(compose)
        except Exception as e:
            raise ValueError(500, f"Failed to write compose file: {e}")

    @classmethod
    def get_status(cls, instance_name: str) -> str:
        """
        Returns 'running' if any container is up, 'stopped' otherwise.
        """
        path = cls.get_instance_dir(instance_name)
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
        path = self.get_instance_dir(instance_name)
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
        path = self.get_instance_dir(instance_name)
        subprocess.run(
            ["docker", "compose", "down"],
            cwd=path,
            check=True
        )

    @classmethod
    def restart(cls, instance_name: str) -> None:
        """
        Restarts the docker compose project.
        """
        cls.stop(instance_name)
        cls.start(instance_name)

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
        path = self.get_instance_dir(instance_name)
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

    @classmethod
    def delete(cls, instance_name: str) -> None:
        """
        Stop containers, prune volumes, and delete the folder.
        """
        path = cls.get_instance_dir(instance_name)
        subprocess.run(["docker", "compose", "down", "--volumes"], cwd=path, check=True)
        shutil.rmtree(path)