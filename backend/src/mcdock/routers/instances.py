"""FastAPI router providing CRUD + live streams for Minecraft instances.

This version aligns with the current DockerService & pydantic models and now
**includes the server.properties GET/PUT endpoints**.
"""
import asyncio
import threading
import re
import json
import logging

from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Security
)
from mcipc.rcon.exceptions import UnknownCommand

from .models import (
    ResponseMessage,
    InstanceCreate,
    InstanceUpdate,
    InstanceInfo,
    CommandRequest,
)
from ..services.docker_service import DockerService
from ..services.models import Instance
from ..services.rcon_service import RconService
from .security import require_user, require_ws_user, UNAUTHORIZED


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/instances", dependencies=[Security(require_user)], responses=UNAUTHORIZED)
ws_router = APIRouter(prefix="/instances", responses=UNAUTHORIZED)

# ---------------------------------------------------------------------------
# Compose management
# ---------------------------------------------------------------------------


@router.post("/create", status_code=201, response_model=ResponseMessage)
async def create_instance(body: InstanceCreate):
    """Create a new Minecraft instance on disk and write its compose file."""
    try:
        DockerService.create_instance(
            instance_name=body.name,
            image=body.image,
            eula=body.eula,
            memory=body.memory,
            env=body.env,
            ports=body.ports,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return ResponseMessage(message=f"Instance '{body.name}' created successfully.")


@router.get("/{instance_name}/compose", response_model=Instance)
async def get_compose(instance_name: str):
    """Return the raw docker-compose.yml for *instance_name*."""
    try:
        return DockerService.get_compose(instance_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/{instance_name}/compose", response_model=ResponseMessage)
async def update_compose(instance_name: str, body: InstanceUpdate):
    """Patch *docker-compose.yml* with any supplied fields."""
    try:
        DockerService.update_compose(
            instance_name,
            eula=body.eula,
            memory=body.memory,
            env=body.env,
            ports=body.ports,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return ResponseMessage(message=f"docker-compose.yml for '{instance_name}' updated.")

# ---------------------------------------------------------------------------
# server.properties management
# ---------------------------------------------------------------------------

@router.get("/{instance_name}/properties", response_model=dict[str, str])
async def get_properties(instance_name: str):
    """Return the key/value map from *server.properties*."""
    try:
        return DockerService.get_properties(instance_name)
    except ValueError as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail=str(e)) from e
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/{instance_name}/properties", response_model=ResponseMessage)
async def update_properties(instance_name: str, props: dict[str, str]):
    """Completely overwrite *server.properties* with *props*."""
    try:
        DockerService.update_properties(instance_name, props)
    except ValueError as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail=str(e)) from e
        raise HTTPException(status_code=500, detail=str(e)) from e
    return ResponseMessage(message="server.properties updated.")

# ---------------------------------------------------------------------------
# Instance lifecycle
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[InstanceInfo])
async def list_instances():
    """list all instances under *MC_ROOT* with their current status."""
    try:
        return [
            InstanceInfo(name=inst_dir.name, status=DockerService.get_status(inst_dir.name))
            for inst_dir in DockerService.get_instance_dirs()
        ]
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{instance_name}/start", response_model=ResponseMessage)
async def start_instance(instance_name: str):
    try:
        DockerService.start(instance_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return ResponseMessage(message="started")


@router.post("/{instance_name}/stop", response_model=ResponseMessage)
async def stop_instance(instance_name: str):
    try:
        DockerService.stop(instance_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return ResponseMessage(message="stopped")


@router.post("/{instance_name}/restart", response_model=ResponseMessage)
async def restart_instance(instance_name: str):
    try:
        DockerService.restart(instance_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return ResponseMessage(message="restarted")


@router.delete("/{instance_name}", status_code=204)
async def delete_instance(instance_name: str):
    try:
        DockerService.delete(instance_name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No such instance: {instance_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# ---------------------------------------------------------------------------
# RCON command
# ---------------------------------------------------------------------------

@router.post("/{instance_name}/cmd", response_model=ResponseMessage)
async def send_command(instance_name: str, body: CommandRequest):
    cmd = body.command.strip()
    if not cmd:
        raise HTTPException(status_code=400, detail="Missing 'command' field")

    try:
        output = RconService.execute(instance_name=instance_name, command=cmd)

    except UnknownCommand as e:                        # bad / unknown command
        raise HTTPException(status_code=400, detail=str(e)) from e

    except Exception as e:                            # timeouts, I/O, etc.
        raise HTTPException(status_code=500, detail=str(e)) from e

    return ResponseMessage(message=output)

# ---------------------------------------------------------------------------
# WebSocket: logs & stats streams
# ---------------------------------------------------------------------------
@ws_router.websocket("/{instance_name}/logs")
async def websocket_logs(
    websocket: WebSocket,
    instance_name: str,
    _ = Security(require_ws_user),   # auth during handshake
):
    await websocket.accept()
    proc = DockerService.stream_logs(instance_name) # Blocking

    loop   = asyncio.get_running_loop()
    queue  = asyncio.Queue[str]()

    # ---------- thread: read docker logs ----------
    def reader():
        try:
            for raw in proc.stdout:                       # blocking read
                line = raw.decode(errors="ignore")
                asyncio.run_coroutine_threadsafe(
                    queue.put(line), loop
                )
        finally:
            proc.stdout.close()

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    # ----------------------------------------------

    try:
        while True:
            line = await queue.get()          # non-blocking for event-loop
            await websocket.send_text(line)
    except WebSocketDisconnect:
        pass
    finally:
        proc.terminate()
        thread.join(timeout=1)

@ws_router.websocket("/{instance_name}/stats")
async def websocket_stats(
    websocket: WebSocket,
    instance_name: str,
    _ = Security(require_ws_user),
):
    await websocket.accept()
    proc = DockerService.stream_stats(instance_name)

    loop   = asyncio.get_running_loop()
    queue  = asyncio.Queue[str]()

    # background thread: push each line into the asyncio queue
    def reader():
        try:
            for raw in proc.stdout:
                asyncio.run_coroutine_threadsafe(queue.put(raw), loop)
        finally:
            proc.stdout.close()

    threading.Thread(target=reader, daemon=True).start()

    # regex to pull the numeric part out of "742.6MiB"
    mem_re = re.compile(r"([\d\.]+)([KMG]i?)B", re.I)
    ansi_re = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    unit_factor = {"Ki": 1/1024, "Mi": 1, "Gi": 1024}

    try:
        while True:
            raw = await queue.get()

            try:
                clean = ansi_re.sub("", raw).strip()
                item = json.loads(clean)
                cpu = float(item["CPUPerc"].rstrip("%"))

                # "742.6MiB / 3.7GiB"  -> 742.6 MiB
                mem_used = item["MemUsage"].split("/")[0].strip()
                val, unit = mem_re.match(mem_used).groups()  # e.g. ("742.6", "Mi")
                mem_mib = float(val) * unit_factor[unit]

                await websocket.send_text(
                    json.dumps({"cpu": cpu, "mem": round(mem_mib, 1)})
                )
            except Exception:
                # ignore malformed lines
                continue
    except WebSocketDisconnect:
        pass
    finally:
        proc.terminate()
