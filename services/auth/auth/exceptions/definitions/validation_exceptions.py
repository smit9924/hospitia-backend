# This file will contain all the exceptions related to the validation
from auth.exceptions.definitions.base import BaseException


class UserWithEmailAlreadyExistsException(BaseException):
    """Raised when a user with the given email already exists."""

    def __init__(self, message: str = "User with given email already exists.") -> None:
        self.message = message


class UserWithUsernameAlreadyExistsException(BaseException):
    """Raised when a user with the given username already exists."""

    def __init__(self, message: str = "User with given username alreadt exists.") -> None:
        self.message = message


class InvalidEmailException(BaseException):
    """Raised when an email address is invalid."""

    def __init__(self, message: str = "Invalid email.") -> None:
        self.message = message