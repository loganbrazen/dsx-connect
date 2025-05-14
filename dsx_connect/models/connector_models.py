from enum import Enum

from pydantic import BaseModel


class ItemActionEnum(str, Enum):
    NOTHING = 'nothing'
    DELETE = 'delete'
    MOVE = 'move'
    TAG = 'tag'


class ItemActionModel(BaseModel):
    action_type: ItemActionEnum = ItemActionEnum.NOTHING
    action_meta: str = None


class ScanRequestModel(BaseModel):
    location: str
    metainfo: str
    connector_url: str = None
