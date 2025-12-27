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
        super().__init__(field, input, ErrorCodes.PUBLIC_EMAIL_NOW_ALLOWED, data, message)
