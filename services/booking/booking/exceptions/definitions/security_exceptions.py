
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


class OrganizationAccessForbiddenException(BaseException):
    """
    Raised when an authenticated user with a valid role attempts to access
    or modify an organization they are not associated with.

    Distinct from `UserUnauthorizedException` (401): this represents a
    correctly authenticated, correctly-roled user who simply does not have
    access to this specific resource (403).
    """

    def __init__(
        self,
        message: str = "You do not have access to this organization."
    ) -> None:
        super().__init__(ErrorCodes.ORGANIZATION_ACCESS_FORBIDDEN, message)
