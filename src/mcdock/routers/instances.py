from fastapi import (
    APIRouter, HTTPException, WebSocket, 
    WebSocketDisconnect, Depends, Query
)
from fastapi.responses import PlainTextResponse

from .models import ResponseMessage, ComposeUpdate, CommandRequest, InstanceCreate, InstanceInfo
from ..core.config import settings, COMPOSE_TEMPLATE
from ..services.docker_service import DockerService
from ..services.rcon_service import RconService
from .security import require_token

router = APIRouter(prefix="/instances", dependencies=[Depends(require_token)])


@router.get(
    "/template",
    response_class=PlainTextResponse,
    status_code=200,
)
async def get_instance_template():
    return COMPOSE_TEMPLATE


@router.post(
    "/create",
    status_code=201,
    response_model=ResponseMessage,
)
async def create_instance(body: InstanceCreate):
    try:
        DockerService.create_instance(body.instance_name, body.compose)
    except ValueError as e:
        raise HTTPException(500, str(e)) from e

    return ResponseMessage(message=f"Instance '{body.instance_name}' created successfully.")


@router.get("/{instance_name}/compose", response_class=PlainTextResponse, status_code=200)
async def get_compose(instance_name: str):
    """
    Return the raw docker-compose.yml for this instance.
    """
    try:
        compose = DockerService.get_compose(instance_name)
        return compose
    except ValueError as e:
        raise HTTPException(500, str(e)) from e


@router.put(
    "/{instance_name}/compose",
    status_code=200,
    response_model=ResponseMessage
)
async def update_compose(
    instance_name: str,
    body: ComposeUpdate
):
    try:
        DockerService.update_compose(instance_name, body.compose)
    except ValueError as e:
        raise HTTPException(500, str(e)) from e
        
    return ResponseMessage(message=f"docker-compose.yml for '{instance_name}' updated.")


@router.get("/", response_model=list[InstanceInfo])
async def list_instances():
    """
    List all Minecraft instances available under MC_ROOT.
    """
    instances = []
    try:
        for inst_dir in DockerService.get_instance_dirs():
            name = inst_dir.name
            status = DockerService.get_status(instance_name=name)
            instances.append(InstanceInfo(name=name, status=status))
        return instances
    except ValueError as e:
        raise HTTPException(500, str(e)) from e


@router.post("/{instance_name}/start", response_model=ResponseMessage)
async def start_instance(instance_name: str):
    """
    Start the specified Minecraft instance.
    """
    try:
        DockerService.start(instance_name=instance_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ResponseMessage(message="started")


@router.post("/{instance_name}/stop", response_model=ResponseMessage)
async def stop_instance(instance_name: str):
    """
    Stop the specified Minecraft instance.
    """
    try:
        DockerService.stop(instance_name=instance_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ResponseMessage(message="stopped")


@router.post("/{instance_name}/restart", response_model=ResponseMessage)
async def restart_instance(instance_name: str):
    """Hard-restart the compose project."""
    try:
        DockerService.restart(instance_name=instance_name)
    except Exception as e:
        raise HTTPException(500, str(e))
    return ResponseMessage(message="restarted")


@router.delete("/{instance_name}", status_code=204)
async def delete_instance(instance_name: str):
    """Destroy the instance and its data directory."""
    try:
        DockerService.delete(instance_name)
    except FileNotFoundError:
        raise HTTPException(404, f"No such instance: {instance_name}")
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/{instance_name}/cmd", response_model=ResponseMessage)
async def send_command(
    instance_name: str,
    body: CommandRequest
):
    """
    Send an RCON command to the specified instance.
    Payload should be JSON: {"command": "<your command>"}
    """
    cmd = body.command
    if not cmd:
        raise HTTPException(status_code=400, detail="Missing 'command' field")
    try:
        output = RconService.execute(instance_name=instance_name, command=cmd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ResponseMessage(message=output)


@router.websocket("/{instance_name}/logs")
async def websocket_logs(websocket: WebSocket, instance_name: str, token: str | None = Query(None)):
    """
    Stream live Docker logs over WebSocket for the given instance.
    """
    await websocket.accept()

    if token != settings.CONTROL_PANEL_BEARER_TOKEN:
        await websocket.close(code=4403)          # 4403 = forbidden
        return

    try:
        process = DockerService.stream_logs(instance_name=instance_name)
        for raw_line in process.stdout:
            line = raw_line.decode(errors="ignore")
            await websocket.send_text(line)
    except WebSocketDisconnect:
        process.terminate()


@router.websocket("/{instance_name}/stats")
async def websocket_stats(websocket: WebSocket, instance_name: str, token: str | None = Query(None)):
    """
    Stream live Docker logs over WebSocket for the given instance.
    """
    await websocket.accept()
    
    if token != settings.CONTROL_PANEL_BEARER_TOKEN:
        await websocket.close(code=4403)          # 4403 = forbidden
        return

    try:
        process = DockerService.stream_stats(instance_name=instance_name)
        for raw_line in process.stdout:
            line = raw_line.decode(errors="ignore")
            await websocket.send_text(line)
    except WebSocketDisconnect:
        process.terminate()