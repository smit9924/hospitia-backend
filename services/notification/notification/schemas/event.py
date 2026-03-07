from typing import Any

from pydantic import BaseModel, Field

from notification.types.enums import Channel, Priority


class NotificationEvent(BaseModel):
    """
    Generic notification event envelope.

    Represents a transport-level message consumed from
    the messaging system and routed to a channel handler.

    Attributes
    ----------
    channel : Channel
        Target delivery channel (email, sms, etc.).
    priority : Priority
        Processing priority influencing queue ordering.
    payload : Dict[str, Any]
        Channel-specific payload passed to handlers.
    """
    channel: Channel
    priority: Priority = Field(
        default=Priority.NORMAL,
        description="Message priority (0-10)",
    )
    payload: dict[str, Any]
