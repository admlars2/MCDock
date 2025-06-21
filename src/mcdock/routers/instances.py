from pathlib import Path

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends, Header
from pydantic import BaseModel

from ..config import settings
from ..schemas.instance import InstanceInfo
from ..services.docker_service import DockerService
from ..services.rcon_service import RconService
from ..services.backup_service import BackupService


def require_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.CONTROL_PANEL_API_KEY:
        raise HTTPException(401, "Invalid API Key")

router = APIRouter(dependencies=[Depends(require_api_key)])


class CommandRequest(BaseModel):
    command: str

class ResponseMessage(BaseModel):
    message: str


def get_instance_dirs() -> list[Path]:
    root = Path(settings.MC_ROOT)
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=500, detail=f"MC_ROOT path not found: {settings.MC_ROOT}")
    return [p for p in root.iterdir() if p.is_dir()]


@router.get("/", response_model=list[InstanceInfo])
async def list_instances():
    """
    List all Minecraft instances available under MC_ROOT.
    """
    instances = []
    for inst_dir in get_instance_dirs():
        name = inst_dir.name
        status = DockerService.get_status(instance_name=name)
        instances.append(InstanceInfo(name=name, status=status))
    return instances


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


@router.post("/{instance_name}/cmd", response_model=ResponseMessage)
async def send_command(
    instance_name: str,
    payload: CommandRequest
):
    """
    Send an RCON command to the specified instance.
    Payload should be JSON: {"command": "<your command>"}
    """
    cmd = payload.command
    if not cmd:
        raise HTTPException(status_code=400, detail="Missing 'command' field")
    try:
        output = RconService.execute(instance_name=instance_name, command=cmd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ResponseMessage(message=output)


@router.websocket("/{instance_name}/logs")
async def websocket_logs(websocket: WebSocket, instance_name: str):
    """
    Stream live Docker logs over WebSocket for the given instance.
    """
    await websocket.accept()
    try:
        process = DockerService.stream_logs(instance_name=instance_name)
        for raw_line in process.stdout:
            line = raw_line.decode(errors="ignore")
            await websocket.send_text(line)
    except WebSocketDisconnect:
        process.terminate()


@router.websocket("/{instance_name}/stats")
async def websocket_stats(websocket: WebSocket, instance_name: str):
    """
    Stream live Docker logs over WebSocket for the given instance.
    """
    await websocket.accept()
    try:
        process = DockerService.stream_stats(instance_name=instance_name)
        for raw_line in process.stdout:
            line = raw_line.decode(errors="ignore")
            await websocket.send_text(line)
    except WebSocketDisconnect:
        process.terminate()


@router.get("/{instance_name}/backups", response_model=list[str])
async def list_backups(instance_name: str):
    """
    List the last BACKUP_RETENTION backups for an instance.
    """
    try:
        files = BackupService.list_backups(instance_name=instance_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return files


@router.post("/{instance_name}/backups", status_code=202, response_model=ResponseMessage)
async def trigger_backup(
    instance_name: str,
    background_tasks: BackgroundTasks,
):
    # 1) validate the instance exists (your existing helper)
    try:
        BackupService()._get_instance_dir(instance_name)
    except FileNotFoundError:
        raise HTTPException(404, f"No such instance: {instance_name}")

    # 2) schedule the actual backup method to run AFTER sending the 202
    background_tasks.add_task(BackupService.trigger_backup, instance_name)

    # 3) immediately return 202—client can poll list_backups or logs if you expose them
    return ResponseMessage(message=f"Backup for '{instance_name}' is being created.")


@router.post("/{instance_name}/{filename}/restore", status_code=202, response_model=ResponseMessage)
async def restore_backup(
    instance_name: str, 
    filename: str,
    background_tasks: BackgroundTasks
):
    """
    Trigger a restoration for a given instance and filename.
    """
    try:
        background_tasks.add_task(BackupService.restore_backup, instance_name, filename)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ResponseMessage(message=f"Restoring '{filename}' for '{instance_name}' in background.")