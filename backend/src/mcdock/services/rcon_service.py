import logging
import time

from mcipc.rcon.je import Client

from ..core.config import settings
from .docker_service import DockerService


logger = logging.getLogger(__name__)


def _read_rcon_from_props(instance_name: str) -> tuple[str, int]:
    """
    Pull rcon.password and rcon.port from server.properties.
    Falls back to global defaults if keys are missing or malformed.
    """
    props = DockerService.get_properties(instance_name)

    # --- password ---
    pwd_raw = props.get("rcon.password") or settings.RCON_PASSWORD
    pwd = pwd_raw.strip() if isinstance(pwd_raw, str) else settings.RCON_PASSWORD

    # --- port ---
    port_raw = props.get("rcon.port")
    try:
        port = int(port_raw.strip()) if port_raw else settings.RCON_PORT
    except (ValueError, AttributeError):
        port = settings.RCON_PORT

    return pwd, port

class RconService:
    """
    Service for sending RCON commands to a Minecraft server instance.
    """
    host = settings.RCON_HOST    

    @classmethod
    def execute(cls, instance_name: str, command: str, *, retries: int = 3, delay: int = 0.5) -> str:
        """
        Send a command via RCON for the specified instance.
        """
        pwd, port = _read_rcon_from_props(instance_name)

        logger.info("Connecting to %s on %s", cls.host, port)

        last_err = None
        for _ in range(retries):
            try:
                with Client(cls.host, port=port, timeout=5) as client:
                    client.login(pwd)
                    return client.run(command)
            except ConnectionRefusedError as e:
                last_err = e
                time.sleep(delay)
        raise last_err