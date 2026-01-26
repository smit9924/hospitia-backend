from enum import Enum


class Channel(str, Enum):
    EMAIL = "email"


class Priority(int, Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10
