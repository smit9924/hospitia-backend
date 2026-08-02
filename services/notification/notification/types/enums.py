from enum import IntEnum, StrEnum


class Channel(StrEnum):
    """
    Supported notification delivery channels.
    """
    EMAIL = "email"


class Priority(IntEnum):
    """
    Message priority levels.

    Higher values indicate higher processing priority
    within RabbitMQ priority queues.
    """
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10
