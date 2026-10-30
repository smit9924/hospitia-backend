
from booking.exceptions.definitions.base import BaseException
from booking.types.error_codes import ErrorCodes


class OrganizationTypeAlreadyExistsException(BaseException):
    """
    Raised when an organization type with the given name already exists.
    """

    def __init__(
        self,
        message: str = "An organization type with this name already exists."
    ) -> None:
        super().__init__(ErrorCodes.ORGANIZATION_TYPE_ALREADY_EXISTS, message)


class OrganizationTypeHasActiveOrganizationsException(BaseException):
    """
    Raised when attempting to delete an organization type that is still
    referenced by one or more active organizations.
    """

    def __init__(
        self,
        message: str = "Cannot delete an organization type that is still in use."
    ) -> None:
        super().__init__(ErrorCodes.ORGANIZATION_TYPE_HAS_ACTIVE_ORGANIZATIONS, message)


class OrganizationHasActiveDependenciesException(BaseException):
    """
    Raised when attempting to delete an organization that has active
    dependencies (e.g. bookings, properties, payments) that would be
    orphaned by the deletion.
    """

    def __init__(
        self,
        message: str = "Cannot delete an organization with active dependencies."
    ) -> None:
        super().__init__(ErrorCodes.ORGANIZATION_HAS_ACTIVE_DEPENDENCIES, message)


class OrganizationMustHaveActiveOwnerException(BaseException):
    """
    Raised when an operation would leave an organization without at least
    one active OWNER mapping.
    """

    def __init__(
        self,
        message: str = "An organization must always have at least one active owner."
    ) -> None:
        super().__init__(ErrorCodes.ORGANIZATION_MUST_HAVE_ACTIVE_OWNER, message)


class UserRoleMismatchForOrganizationException(BaseException):
    """
    Raised when a selected user does not have the role required for the
    requested organization assignment (e.g. an Admin selects a non-Owner
    user as an organization's Owner).
    """

    def __init__(
        self,
        message: str = "The selected user does not have the required role for this assignment."
    ) -> None:
        super().__init__(ErrorCodes.USER_ROLE_MISMATCH_FOR_ORGANIZATION, message)


class ActiveOrganizationRequiredException(BaseException):
    """
    Raised when an endpoint that requires an active organization receives
    no `X-Active-Organization-Guid` header, or a value that is not a UUID.
    """

    def __init__(
        self,
        message: str = "An active organization is required for this request."
    ) -> None:
        super().__init__(ErrorCodes.ACTIVE_ORGANIZATION_REQUIRED, message)
