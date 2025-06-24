from pydantic import BaseModel, Field, field_validator

from ..core.models import Port, EnvVar, ConnectionType

class InstanceCreate(BaseModel):
    name:        str  = Field(pattern=r"^[A-Za-z0-9_-]+$")
    image:       str = Field(default="itzg/minecraft-server:latest")
    eula:        bool
    memory:      str = Field(default="4G", pattern=r"^\d+[MG]$")
    env:         list[EnvVar] = []
    ports:       list[Port] = Field(default_factory=lambda: [Port(min=25565, max=25565, type=ConnectionType.TCP)])

    @classmethod
    @field_validator("image")
    def validate_image(cls, v: str) -> str:
        if not v.startswith("itzg/minecraft-server"):
            raise ValueError("Must be a minecraft server.")

class InstanceUpdate(BaseModel):
    """ Update that always performs a rewrite. """
    eula: bool
    memory:     str = Field(pattern=r"^\d+[MG]$")
    env:        list[EnvVar]
    ports:      list[Port]

class InstanceInfo(BaseModel):
    """
    Schema representing a Minecraft instance and its current status.
    """
    name: str = Field(description="Name of the instance folder")
    status: str = Field(description="Current status: e.g., 'running' or 'stopped'")

class CommandRequest(BaseModel):
    command: str

class CronSchedule(BaseModel):
    cron: str  # e.g. "0 0 * * *" for midnight daily

class ResponseMessage(BaseModel):
    message: str

class ScheduledJob(BaseModel):
    id: str
    schedule: str         # the trigger spec (cron or date)
    next_run: str | None