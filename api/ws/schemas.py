"""
Pydantic-модели и Enum для сообщений.
"""

from pydantic import BaseModel
from enum import Enum
from typing import Optional, Dict, Any, Union


class Event(str, Enum):
    GET_PACS_INIT_VALUE = "getPacsInitValue"
    GET_PACS_EMPLOYEE_LAST_EVENT = "getPacsEmployeeLastEvent"
    GET_PACS_LAST_EVENT = "event_pacs_last_event"
    GET_DEPARTMENT_STRUCTURE_BY_UPN = "getDepartmentStructureByUPN"
    GET_FILTERED_REQUEST_INITIATOR = "getFilteredRequestInitiator"

    # Celery Beat
    EVENT_PROVIDER_INFO = "event_provider_info"

    # getFilteredRequestInitiator
    # добавьте другие события при необходимости

class ClientMessage(BaseModel):
    event: Event
    data: Optional[Union[Dict[str, Any], str, int]] = None