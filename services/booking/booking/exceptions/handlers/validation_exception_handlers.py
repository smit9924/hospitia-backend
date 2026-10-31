from fastapi import Request, status
from fastapi.responses import JSONResponse

from booking.exceptions.definitions.validation_exceptions import (
    ActiveOrganizationRequiredException,
    CurrencyUnitAlreadyExistsException,
    CurrencyUnitInUseException,
    OrganizationHasActiveDependenciesException,
    OrganizationMustHaveActiveOwnerException,
    OrganizationTypeAlreadyExistsException,
    OrganizationTypeHasActiveOrganizationsException,
    RoomAmenityAlreadyExistsException,
    RoomAmenityInUseException,
    UserRoleMismatchForOrganizationException,
)
from booking.schemas.common_schemas import ApiErrorResponse


def organization_type_already_exists_exception_handler(
    _request: Request,
    exc: OrganizationTypeAlreadyExistsException,
) -> JSONResponse:
    """
    Handle organization type already exists exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(),
    )


def organization_type_has_active_organizations_exception_handler(
    _request: Request,
    exc: OrganizationTypeHasActiveOrganizationsException,
) -> JSONResponse:
    """
    Handle organization type has active organizations exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(),
    )


def organization_has_active_dependencies_exception_handler(
    _request: Request,
    exc: OrganizationHasActiveDependenciesException,
) -> JSONResponse:
    """
    Handle organization has active dependencies exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(),
    )


def organization_must_have_active_owner_exception_handler(
    _request: Request,
    exc: OrganizationMustHaveActiveOwnerException,
) -> JSONResponse:
    """
    Handle organization must have active owner exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(),
    )


def user_role_mismatch_for_organization_exception_handler(
    _request: Request,
    exc: UserRoleMismatchForOrganizationException,
) -> JSONResponse:
    """
    Handle user role mismatch for organization exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response.model_dump(),
    )


def active_organization_required_exception_handler(
    _request: Request,
    exc: ActiveOrganizationRequiredException,
) -> JSONResponse:
    """
    Handle active organization required exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response.model_dump(),
    )


def currency_unit_already_exists_exception_handler(
    _request: Request,
    exc: CurrencyUnitAlreadyExistsException,
) -> JSONResponse:
    """
    Handle currency unit already exists exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(),
    )


def currency_unit_in_use_exception_handler(
    _request: Request,
    exc: CurrencyUnitInUseException,
) -> JSONResponse:
    """
    Handle currency unit in use exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(),
    )


def room_amenity_already_exists_exception_handler(
    _request: Request,
    exc: RoomAmenityAlreadyExistsException,
) -> JSONResponse:
    """
    Handle room amenity already exists exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(),
    )


def room_amenity_in_use_exception_handler(
    _request: Request,
    exc: RoomAmenityInUseException,
) -> JSONResponse:
    """
    Handle room amenity in use exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(),
    )
