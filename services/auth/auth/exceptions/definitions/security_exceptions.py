
from auth.exceptions.definitions.base import BaseException
from auth.types.error_codes import ErrorCodes


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


class InvalidCredentialsException(BaseException):
    """
    Raised when authentication fails due to incorrect credentials.

    This exception is triggered when the provided username/email
    or password does not match any valid user account.
    """

    def __init__(
        self,
        message: str = "Incorrect username or password."
    ) -> None:
        super().__init__(ErrorCodes.INVALID_CREDENTIALS, message)


class UserInactiveException(BaseException):
    """
    Raised when a registered user attempts to access the system
    but their account is inactive.

    This exception is triggered when the user's account is disabled,
    suspended, or not yet activated, indicated by the `isActive`
    flag in the database being set to `false`.
    """

    def __init__(
        self,
        message: str = "Your account is inactive. Please contact support or activate your account."
    ) -> None:
        super().__init__(ErrorCodes.USER_INACTIVE, message)
