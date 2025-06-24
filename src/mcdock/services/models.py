from pydantic import BaseModel

from ..core.models import EnvVar, Port


class Instance(BaseModel):
    name:        str
    image:       str
    eula:        bool
    memory:      str
    env:         list[EnvVar]
    ports:       list[Port]