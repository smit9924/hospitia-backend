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
    RoomAlreadyExistsException,
    RoomAmenityAlreadyExistsException,
    RoomAmenityInUseException,
    RoomOrganizationRequiredException,
    RoomTypeAlreadyExistsException,
    RoomTypeAmenityNotAvailableException,
    RoomTypeInUseException,
    RoomTypeNotAvailableForRoomException,
    RoomTypeOrganizationRequiredException,
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

    Description
    -----------
    Generates a standardized API error response when another active
    currency unit already uses the requested ISO 4217 alphabetic or numeric
    code. The message says which code clashes.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    exc : CurrencyUnitAlreadyExistsException
        Exception describing the clashing currency code.

    Returns
    -------
    JSONResponse
        HTTP 409 Conflict response with a structured error payload.
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

    Description
    -----------
    Generates a standardized API error response when a currency unit
    cannot be deleted because an active room type is priced in it.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    exc : CurrencyUnitInUseException
        Exception describing why the currency unit is still in use.

    Returns
    -------
    JSONResponse
        HTTP 409 Conflict response with a structured error payload.
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

    Description
    -----------
    Generates a standardized API error response when the amenity name is
    already used in its scope (case-insensitively), or a custom amenity
    repeats a default amenity name.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    exc : RoomAmenityAlreadyExistsException
        Exception describing the clashing amenity name.

    Returns
    -------
    JSONResponse
        HTTP 409 Conflict response with a structured error payload.
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

    Description
    -----------
    Generates a standardized API error response when a room amenity
    cannot be deleted because an active room type still lists it.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    exc : RoomAmenityInUseException
        Exception describing why the amenity is still in use.

    Returns
    -------
    JSONResponse
        HTTP 409 Conflict response with a structured error payload.
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


def room_type_already_exists_exception_handler(
    _request: Request,
    exc: RoomTypeAlreadyExistsException,
) -> JSONResponse:
    """
    Handle room type already exists exceptions.

    Description
    -----------
    Generates a standardized API error response when another active room
    type of the same organization already uses the name
    (case-insensitively).

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    exc : RoomTypeAlreadyExistsException
        Exception describing the clashing room type name.

    Returns
    -------
    JSONResponse
        HTTP 409 Conflict response with a structured error payload.
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


def room_type_amenity_not_available_exception_handler(
    _request: Request,
    exc: RoomTypeAmenityNotAvailableException,
) -> JSONResponse:
    """
    Handle room type amenity not available exceptions.

    Description
    -----------
    Generates a standardized API error response when a room type selects
    an amenity that does not exist, was deleted, or is a custom amenity of
    another organization.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    exc : RoomTypeAmenityNotAvailableException
        Exception describing the unavailable amenity selection.

    Returns
    -------
    JSONResponse
        HTTP 400 Bad Request response with a structured error payload.
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


def room_type_organization_required_exception_handler(
    _request: Request,
    exc: RoomTypeOrganizationRequiredException,
) -> JSONResponse:
    """
    Handle room type organization required exceptions.

    Description
    -----------
    Generates a standardized API error response when an admin creates a
    room type without choosing the organization it belongs to.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    exc : RoomTypeOrganizationRequiredException
        Exception describing the missing organization.

    Returns
    -------
    JSONResponse
        HTTP 400 Bad Request response with a structured error payload.
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


def room_already_exists_exception_handler(
    _request: Request,
    exc: RoomAlreadyExistsException,
) -> JSONResponse:
    """
    Handle room already exists exceptions.

    Description
    -----------
    Generates a standardized API error response when another active room of the same organization already uses the room
    number (case-insensitively).

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    exc : RoomAlreadyExistsException
        Exception describing the clashing room number.

    Returns
    -------
    JSONResponse
        HTTP 409 Conflict response with a structured error payload.
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


def room_organization_required_exception_handler(
    _request: Request,
    exc: RoomOrganizationRequiredException,
) -> JSONResponse:
    """
    Handle room organization required exceptions.

    Description
    -----------
    Generates a standardized API error response when an admin creates a room without choosing the organization it belongs
    to.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    exc : RoomOrganizationRequiredException
        Exception describing the missing organization.

    Returns
    -------
    JSONResponse
        HTTP 400 Bad Request response with a structured error payload.
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


def room_type_not_available_for_room_exception_handler(
    _request: Request,
    exc: RoomTypeNotAvailableForRoomException,
) -> JSONResponse:
    """
    Handle room type not available for room exceptions.

    Description
    -----------
    Generates a standardized API error response when a room selects a room type that does not exist, was deleted, or
    belongs to another organization.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    exc : RoomTypeNotAvailableForRoomException
        Exception describing the unavailable room type.

    Returns
    -------
    JSONResponse
        HTTP 400 Bad Request response with a structured error payload.
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


def room_type_in_use_exception_handler(
    _request: Request,
    exc: RoomTypeInUseException,
) -> JSONResponse:
    """
    Handle room type in use exceptions.

    Description
    -----------
    Generates a standardized API error response when a room type cannot be deleted because active rooms still use it.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    exc : RoomTypeInUseException
        Exception describing the room type that is still in use.

    Returns
    -------
    JSONResponse
        HTTP 409 Conflict response with a structured error payload.
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
