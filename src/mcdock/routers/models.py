from pydantic import BaseModel, Field


class InstanceCreate(BaseModel):
    instance_name: str = Field(
        regex=r"^[A-Za-z0-9_-]+$",
        description="Only letters, numbers, underscore or hyphen"
    )
    compose: str = Field(
        description="Full docker-compose.yml contents for this instance"
    )

class ComposeUpdate(BaseModel):
    compose: str = Field(
        description="Full contents of docker-compose.yml to write"
    )

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