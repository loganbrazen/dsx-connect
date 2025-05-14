from pydantic import BaseModel
from enum import Enum


class StatusResponseEnum(str, Enum):
    SUCCESS: str = 'success'
    ERROR: str = 'error'
    NOTHING: str = 'nothing'


class StatusResponse(BaseModel):
    status: StatusResponseEnum
    message: str
    description: str | None = None
    id: str | None = None
