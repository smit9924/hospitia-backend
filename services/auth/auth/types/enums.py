from enum import IntEnum


class AuthType(IntEnum):
    """
    Authentication method types supported by the system.

    This enum defines the available authentication strategies for user login.
    Values are stored as integers in the database for efficiency.

    Attributes
    ----------
    MANUAL : int
        Traditional email/password authentication.
        Value: 1
    GOOGLE : int
        OAuth 2.0 authentication via Google.
        Value: 2
    FACEBOOK : int
        OAuth 2.0 authentication via Facebook.
        Value: 3
    X : int
        OAuth 2.0 authentication via X (formerly Twitter).
        Value: 4
    """
    MANUAL = 1
    GOOGLE = 2
    FACEBOOK = 3
    X = 4


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
