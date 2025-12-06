from enum import Enum

class AuthType(Enum):
    """
    Enumeration for different authentication types.
    """
    MANUAL=1
    GOOGLE=2
    FACEBOOK=3
    X=4

class UserType(Enum):
    """
    Enumeration for different user roles/types.
    """
    ADMIN=1
    OWNER=2
    MANAGER=3
    CUSTOMER=4