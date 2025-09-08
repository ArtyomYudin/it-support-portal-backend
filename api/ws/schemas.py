"""
Pydantic-модели и Enum для сообщений.
"""

from pydantic import BaseModel
from enum import Enum
from typing import Optional, Dict, Any


class Event(str, Enum):
    GET_PACS_INIT_VALUE = "getPacsInitValue"
    GET_DEPARTMENT_STRUCTURE_BY_UPN = "getDepartmentStructureByUPN"
    # добавьте другие события при необходимости

class ClientMessage(BaseModel):
    event: Event
    data: Optional[Dict[str, Any]] = None