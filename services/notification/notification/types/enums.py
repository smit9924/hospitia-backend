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


class EnvironmentName(StrEnum):
    """Runtime environment that selects logging handlers and related behaviour."""

    LOCAL = "local"
    PRODUCTION = "production"


class LogFormatName(StrEnum):
    """Log line encoding written to stdout and, locally, to the log file."""

    CONSOLE = "console"
    JSON = "json"


class LogLevelName(StrEnum):
    """Python logging levels accepted by LOG_LEVEL."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
