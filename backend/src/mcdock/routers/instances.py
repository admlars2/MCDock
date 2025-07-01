"""FastAPI router providing CRUD + live streams for Minecraft instances.

This version aligns with the current DockerService & pydantic models and now
**includes the server.properties GET/PUT endpoints**.
"""
from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Security,
    Depends
)

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return ResponseMessage(message=output)

# ---------------------------------------------------------------------------
# WebSocket: logs & stats streams
# ---------------------------------------------------------------------------
@ws_router.websocket("/{instance_name}/logs")
async def websocket_logs(
    websocket: WebSocket,
    instance_name: str,
    _ = Depends(require_ws_user),
):
    await websocket.accept()
    process = await DockerService.stream_logs_async(instance_name)

    try:
        while True:
            line = await process.stdout.readline()
            if line:
                await websocket.send_text(line.decode(errors="ignore"))
            else:
                break
    
    except WebSocketDisconnect:
        pass
    finally:
        if process.returncode is None:
            process.terminate()

@ws_router.websocket("/{instance_name}/stats")
async def websocket_stats(
    ws: WebSocket, 
    instance_name: str,
    _ = Security(require_ws_user)
):
    await ws.accept()
    process = None
    try:
        process = DockerService.stream_stats(instance_name)
        for raw_line in process.stdout:
            await ws.send_text(raw_line.decode(errors="ignore"))
    except WebSocketDisconnect:
        pass
    finally:
        if process:
            process.terminate()
