"""
Pydantic-модели и Enum для сообщений.
"""

from pydantic import BaseModel
from enum import Enum
from typing import Optional, Dict, Any, Union


class Event(str, Enum):

    # Celery Worker & Beat
    EVENT_PROVIDER_INFO = "event_provider_info"
    EVENT_HARDWARE_GROUP_ALARM = "event_hardware_group_alarm"
    EVENT_CISCO_VPN_ACTIVE_SESSION = "event_cisco_vpn_active_session"
    EVENT_AVAYA_E1_CHANNEL_INFO = "event_avaya_e1_channel_info"
    EVENT_DHCP_SCOPES_COLLECTED = "event_dhcp_scopes_collected"
    EVENT_DHCP_STATISTICS_COLLECTED = "event_dhcp_statistics_collected"
    EVENT_DHCP_LEASES_COLLECTED = "event_dhcp_leases_collected"

class ClientMessage(BaseModel):
    event: Event
    data: Optional[Union[Dict[str, Any], str, int]] = None