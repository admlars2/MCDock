from pydantic import BaseModel, Field


class InstanceInfo(BaseModel):
    """
    Schema representing a Minecraft instance and its current status.
    """
    name: str = Field(description="Name of the instance folder")
    status: str = Field(description="Current status: e.g., 'running' or 'stopped'")