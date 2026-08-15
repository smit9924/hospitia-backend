
from booking.exceptions.definitions.base import BaseException
from booking.types.error_codes import ErrorCodes


class UserUnauthorizedException(BaseException):
    """
    Raised when a user attempts to access a protected resource without
    valid authentication or sufficient authorization.

    This exception represents authentication failures such as missing,
    expired, or invalid credentials.
    """

    def __init__(
        self,
        message: str = "You are not authorized to perform this action. Please authenticate and try again."
    ) -> None:
        super().__init__(ErrorCodes.UNAUTHORIZED, message)
