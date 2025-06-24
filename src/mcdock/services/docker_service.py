import subprocess
import shutil
import yaml
from collections import OrderedDict
from pathlib import Path
from copy import deepcopy

from .models import Instance
from ..core.config import settings
from ..core.models import EnvVar, Port, ConnectionType
from ..templates.compose import COMPOSE_TEMPLATE


class DockerService:
    """
    Service for managing Docker-compose based Minecraft instances.
    """
    root = Path(settings.MC_ROOT)

    @classmethod
    def get_instance_dirs(cls) -> list[Path]:
        if not cls.root.exists() or not cls.root.is_dir():
            raise ValueError(f"MC_ROOT path not found: {settings.MC_ROOT}")
        return [p for p in cls.root.iterdir() if p.is_dir()]

    @classmethod
    def get_instance_dir(cls, instance_name: str) -> Path:
        path = cls.root / instance_name
        if not path.exists() or not path.is_dir():
            raise FileNotFoundError(f"Instance not found: {instance_name}")
        return path
    
    @classmethod
    def _check_ports(cls, ports: list[Port]):
        used = set()
        for d in cls.get_instance_dirs():
            yml = yaml.safe_load((d / "docker-compose.yml").read_text())
            for line in yml["services"]["mc-server"]["ports"]:
                host, proto = line.split("/")[0].split(":")[0], line.split("/")[1]
                used.add((int(host), proto))
        for p in ports:
            if (p.value, p.type) in used:
                raise ValueError(f"Port {p.value}/{p.type} already in use")
    
    @classmethod
    def create_instance(cls, instance_name: str, image: str, eula: bool, memory: str, env: list[EnvVar], ports: list[Port]) -> None:
        inst_dir = cls.root / instance_name

        # 1) create the folder
        try:
            inst_dir.mkdir(parents=True, exist_ok=False)
            (inst_dir / "data").mkdir()
        except Exception as e:
            raise ValueError(f"Failed to create instance directory: {e}")
    
        instance = Instance(
            name=instance_name,
            image=image,
            eula=eula,
            memory=memory,
            env=env,
            ports=ports
        )

        compose_txt = COMPOSE_TEMPLATE.render(**instance.model_dump())

        # 2) write the user-supplied compose file
        try:
            (inst_dir / "docker-compose.yml").write_text(compose_txt)
        except Exception as e:
            raise ValueError(500, f"Failed to write compose file: {e}")
        
    @classmethod
    def get_compose(cls, instance_name: str) -> Instance:
        """
        Parse docker-compose.yml and return an Instance object
        (name, image, eula, memory, env, ports).
        """
        compose_path = cls.root / instance_name / "docker-compose.yml"
        if not compose_path.exists():
            raise FileNotFoundError(f"No docker-compose.yml in '{instance_name}'")

        try:
            data = yaml.safe_load(compose_path.read_text())
        except yaml.YAMLError as e:
            raise ValueError(f"Malformed compose file: {e}") from e

        srv = data["services"]["mc-server"]        # fixed name from the template
        env = srv.get("environment", {})

        # --- rebuild Instance fields ----------------------------------
        instance = Instance(
            name           = instance_name,
            image          = srv["image"],
            eula           = env.get("EULA", "FALSE").upper() == "TRUE",
            memory         = env.get("MEMORY", "4G"),
            env            = [
                EnvVar(key=k, value=v)
                for k, v in env.items()
                if k not in {"EULA", "MEMORY"}            # exclude locked vars
            ],
            ports          = [
                Port(value=int(binding.split(":")[0]),
                    type = ConnectionType(binding.split("/")[1]))
                for binding in srv.get("ports", [])
            ],
        )
        return instance
        
    @classmethod
    def update_compose(
        cls,
        instance_name: str,
        eula: bool | None = None,
        memory: str | None = None,
        env: list[EnvVar] | None = None,
        ports: list[Port] | None = None,
    ) -> None:
        """
        Patch docker-compose.yml with the provided fields.
        Only supplied args are modified; others stay unchanged.
        """
        inst_dir     = cls.get_instance_dir(instance_name)
        compose_path = inst_dir / "docker-compose.yml"
        if not compose_path.exists():
            raise FileNotFoundError(f"No docker-compose.yml in '{instance_name}'")

        # --- load old compose -----------------------------------------
        try:
            data = yaml.safe_load(compose_path.read_text())
        except yaml.YAMLError as e:
            raise ValueError(f"Malformed compose file: {e}") from e

        srv = data["services"]["mc-server"]
        env_block = srv.setdefault("environment", {})

        # --- patch primitives -----------------------------------------
        if eula is not None:
            env_block["EULA"]   = "TRUE" if eula else "FALSE"
        if memory is not None:
            env_block["MEMORY"] = memory

        # --- patch env whitelist --------------------------------------
        if env is not None:
            env_block = {k: v for k, v in env_block.items()
                        if k in {"EULA", "MEMORY"}}          # keep locked keys
            for var in env:
                env_block[var.key] = var.value
            srv["environment"] = deepcopy(env_block)

        # --- patch ports ----------------------------------------------
        if ports is not None:
            cls._check_ports(ports, exclude_instance=instance_name)
            srv["ports"] = [
                f"{p.value}:{p.value}/{p.type}" for p in ports
            ]

        # --- write atomically -----------------------------------------
        tmp = compose_path.with_suffix(".tmp")
        tmp.write_text(
            yaml.safe_dump(data, sort_keys=False, default_flow_style=False)
        )
        tmp.replace(compose_path)
        
    @classmethod
    def get_properties(cls, instance_name: str) -> dict[str, str]:
        """
        Return key/value pairs from server.properties, ignoring blanks/comments.
        """
        inst_dir = cls.root / instance_name
        prop_path = inst_dir / "data" / "server.properties"

        if not prop_path.exists():
            raise ValueError(404, f"No server.properties in '{instance_name}'")

        props: dict[str, str] = OrderedDict()
        for line in prop_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                # Ill-formed line → ignore or raise; here we ignore
                continue
            key, value = line.split("=", 1)
            props[key.strip()] = value.strip()

        return props
    
    @classmethod
    def update_properties(cls, instance_name: str, props: dict[str, str]) -> None:
        """
        Overwrite server.properties with the given mapping.
        Comments are dropped; only key=value lines are kept.
        """
        inst_dir = cls.root / instance_name
        prop_path = inst_dir / "data" / "server.properties"

        if not prop_path.exists():
            raise ValueError(404, f"No server.properties in '{instance_name}'")
        
        try:
            tmp = prop_path.with_suffix(".tmp")
            tmp.write_text("\n".join(f"{k}={v}" for k, v in props.items()) + "\n")
            tmp.replace(prop_path)
        except Exception as e:
            raise ValueError(500, f"Failed to write server.properties: {e}")

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
    def start(cls, instance_name: str) -> None:
        """
        Starts the Docker-compose project (detached).
        """
        path = cls.get_instance_dir(instance_name)
        subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=path,
            check=True
        )

    @classmethod
    def stop(cls, instance_name: str) -> None:
        """
        Stops the Docker-compose project and removes containers.
        """
        path = cls.get_instance_dir(instance_name)
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
    def stream_logs(cls, instance_name: str) -> subprocess.Popen:
        return subprocess.Popen(
            ["docker", "logs", "-f", instance_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
    
    @classmethod
    def stream_stats(cls, instance_name: str) -> subprocess.Popen:
        """
        Return a subprocess that streams live Docker stats for the given instance.
        """
        path = cls.get_instance_dir(instance_name)
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