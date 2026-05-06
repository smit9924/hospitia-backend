from typing import Any

from auth.exceptions.definitions.base import BaseException
from auth.types.error_codes import ErrorCodes


class PublicEmailNotAllowedException(BaseException):
    """
    Raised when a public email domain is used where a business or organization
    email address is required.
    """

    def __init__(
        self,
        field: str,
        input: str,
        data: Any = None,
        message: str = "Public email domains are not allowed. Please use a business email address."
    ) -> None:
        self. field = field
        self.input = input
        self.data = data
        super().__init__(ErrorCodes.PUBLIC_EMAIL_NOW_ALLOWED, message)


class UserWithEmailAlreadyExistsException(BaseException):
    """Raised when a user with the given email already exists."""

    def __init__(
        self,
        message: str = "A user with the provided email address already exists."
    ) -> None:
        super().__init__(ErrorCodes.USER_WITH_EMAIL_ALREADY_EXIST, message)


class UserWithUsernameAlreadyExistsException(BaseException):
    """Raised when a user with the given username already exists."""

    def __init__(
        self,
        message: str = "A user with the provided username already exists."
    ) -> None:
        super().__init__(ErrorCodes.USER_WITH_USENAME_ALREADY_EXIST, message)
