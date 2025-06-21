# File: src/mc_panel/services/rcon_service.py
from pathlib import Path
from mcipc.rcon.je import Client

from ..config import settings


def _read_rcon_from_props(props_path: Path) -> tuple[str, int]:
    """
    Read RCON password and port from a server.properties file.
    """
    pwd = None
    port = None
    for ln in props_path.read_text().splitlines():
        if ln.startswith("rcon.password="):
            pwd = ln.split("=", 1)[1].strip()
        elif ln.startswith("rcon.port="):
            try:
                port = int(ln.split("=", 1)[1].strip())
            except ValueError:
                port = None
    # Use parsed values or fall back to global settings
    return pwd or settings.RCON_PASSWORD, port or settings.RCON_PORT


class RconService:
    """
    Service for sending RCON commands to a Minecraft server instance.
    """
    host = settings.RCON_HOST    

    @classmethod
    def execute(cls, instance_name: str, command: str) -> str:
        """
        Send a command via RCON for the specified instance.
        """
        inst_dir = Path(settings.MC_ROOT) / instance_name
        props = inst_dir / "data" / "server.properties"
        pwd, port = _read_rcon_from_props(props)

        # Connect and run the command
        with Client(cls.host, port=port) as client:
            client.login(pwd)
            return client.run(command)
