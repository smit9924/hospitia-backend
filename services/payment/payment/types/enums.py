from enum import IntEnum, StrEnum


class UserType(IntEnum):
    """
    User role types for role-based access control (RBAC).

    This enum defines user permission levels in the system hierarchy.
    Values are stored as integers in the database for efficiency.

    Attributes
    ----------
    ADMIN : int
        System administrator with full access to all features and settings.
        Can manage all users, content, and system configurations.
        Value: 1
    OWNER : int
        Business or organization owner with elevated privileges. Can manage
        organizational settings and create users under organization.
        Value: 2
    MANAGER : int
        Manager role with permissions to oversee specific areas or teams.
        Can manage customers and content within their assigned scope.
        Value: 3
    CUSTOMER : int
        End user or client with standard access to services and features.
        Value: 4
    """
    ADMIN = 1
    OWNER = 2
    MANAGER = 3
    CUSTOMER = 4

class TokenType(IntEnum):
    """
    JWT token types for distinguishing access and refresh tokens.

    This enum defines the purpose of JWT tokens issued by the authentication
    system. Values are stored as integers in the database for efficiency.

    Attributes
    ----------
    ACCESS : int
        Access token used for authenticating API requests. Short-lived token
        that grants access to protected resources.
        Value: 1
    REFRESH : int
        Refresh token used to obtain new access tokens after expiration.
        Long-lived token that can be securely stored by clients.
        Value: 2
    """
    ACCESS = 1
    REFRESH = 2


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
