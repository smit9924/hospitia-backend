from pydantic import BaseModel, Field
from typing import Dict, Any

from app.models.enums import Channel, Priority


class NotificationEvent(BaseModel):
    channel: Channel
    priority: Priority = Field(
        default=Priority.NORMAL,
        description="Message priority (0–10)"
    )
    payload: Dict[str, Any]
