
from dashboard.exceptions.definitions.base import BaseException
from dashboard.types.error_codes import ErrorCodes


class UserNotFoundException(BaseException):
    """
    Raised when a requested user resource cannot be found in the database.
    """

    def __init__(
        self,
        message: str = "The requested user was not found."
    ) -> None:
        super().__init__(ErrorCodes.USER_NOT_FOUND, message)
