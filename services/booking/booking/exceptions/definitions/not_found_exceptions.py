
from booking.exceptions.definitions.base import BaseException
from booking.types.error_codes import ErrorCodes


class UserNotFoundException(BaseException):
    """
    Raised when a requested user resource cannot be found in the database.
    """

    def __init__(
        self,
        message: str = "The requested user was not found."
    ) -> None:
        super().__init__(ErrorCodes.USER_NOT_FOUND, message)


class OrganizationTypeNotFoundException(BaseException):
    """
    Raised when a requested organization type cannot be found in the
    database, or has already been deleted.
    """

    def __init__(
        self,
        message: str = "The requested organization type was not found."
    ) -> None:
        super().__init__(ErrorCodes.ORGANIZATION_TYPE_NOT_FOUND, message)


class AddressNotFoundException(BaseException):
    """
    Raised when a requested address cannot be found in the database.
    """

    def __init__(
        self,
        message: str = "The requested address was not found."
    ) -> None:
        super().__init__(ErrorCodes.ADDRESS_NOT_FOUND, message)


class OrganizationNotFoundException(BaseException):
    """
    Raised when a requested organization cannot be found in the database,
    or has already been deleted.
    """

    def __init__(
        self,
        message: str = "The requested organization was not found."
    ) -> None:
        super().__init__(ErrorCodes.ORGANIZATION_NOT_FOUND, message)


class OrganizationUserMappingNotFoundException(BaseException):
    """
    Raised when a requested organization-user mapping cannot be found in
    the database.
    """

    def __init__(
        self,
        message: str = "The requested organization membership was not found."
    ) -> None:
        super().__init__(ErrorCodes.ORGANIZATION_USER_MAPPING_NOT_FOUND, message)
