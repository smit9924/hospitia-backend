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


class WeakPasswordException(BaseException):
    """Raised when a provided password does not meet strength requirements."""

    def __init__(
        self,
        message: str = "The provided password is too weak. Password must be at least 8 characters long and include uppercase letters, lowercase letters, numbers, and special characters."
    ) -> None:
        super().__init__(ErrorCodes.WEAK_PASSWORD, message)


class InvalidUsernameException(BaseException):
    """Raised when a provided username does not meet validation requirements."""

    def __init__(
        self,
        message: str = "The provided username is invalid. Username must be between 3 and 50 characters long and can only contain letters, digits, and underscores. It must start with a letter and end with a letter or digit."
    ) -> None:
        super().__init__(ErrorCodes.INVALID_USERNAME, message)


class EmailAlreadyVerifiedException(BaseException):
    """Raised when email verification is requested for an already verified email."""

    def __init__(
        self,
        message: str = "Your email address has already been verified."
    ) -> None:
        super().__init__(ErrorCodes.EMAIL_ALREADY_VERIFIED, message)


class InvalidOtpException(BaseException):
    """Raised when a provided OTP is invalid, expired, or already used."""

    def __init__(
        self,
        message: str = "The provided OTP is invalid or has expired."
    ) -> None:
        super().__init__(ErrorCodes.INVALID_OTP, message)
