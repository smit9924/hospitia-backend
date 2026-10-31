from fastapi import Request, status
from fastapi.responses import JSONResponse

from booking.exceptions.definitions.not_found_exceptions import (
    AddressNotFoundException,
    CurrencyUnitNotFoundException,
    OrganizationNotFoundException,
    OrganizationTypeNotFoundException,
    OrganizationUserMappingNotFoundException,
    RoomAmenityNotFoundException,
    RoomTypeNotFoundException,
    UserNotFoundException,
)
from booking.schemas.common_schemas import ApiErrorResponse


def user_not_found_exception_handler(
    _request: Request,
    exc: UserNotFoundException,
) -> JSONResponse:
    """
    Handle user not found exceptions.

    Description
    -----------
    Generates a standardized API error response when a requested user
    resource cannot be found in the database.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    exc : UserNotFoundException
        Exception containing details about the user not found error, including
        the error code and user-facing message.

    Returns
    -------
    JSONResponse
        HTTP 404 Not Found response with a structured error payload describing
        the missing user resource.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=response.model_dump(),
    )


def organization_type_not_found_exception_handler(
    _request: Request,
    exc: OrganizationTypeNotFoundException,
) -> JSONResponse:
    """
    Handle organization type not found exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=response.model_dump(),
    )


def address_not_found_exception_handler(
    _request: Request,
    exc: AddressNotFoundException,
) -> JSONResponse:
    """
    Handle address not found exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=response.model_dump(),
    )


def organization_not_found_exception_handler(
    _request: Request,
    exc: OrganizationNotFoundException,
) -> JSONResponse:
    """
    Handle organization not found exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=response.model_dump(),
    )


def organization_user_mapping_not_found_exception_handler(
    _request: Request,
    exc: OrganizationUserMappingNotFoundException,
) -> JSONResponse:
    """
    Handle organization-user mapping not found exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=response.model_dump(),
    )


def currency_unit_not_found_exception_handler(
    _request: Request,
    exc: CurrencyUnitNotFoundException,
) -> JSONResponse:
    """
    Handle currency unit not found exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=response.model_dump(),
    )


def room_amenity_not_found_exception_handler(
    _request: Request,
    exc: RoomAmenityNotFoundException,
) -> JSONResponse:
    """
    Handle room amenity not found exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=response.model_dump(),
    )


def room_type_not_found_exception_handler(
    _request: Request,
    exc: RoomTypeNotFoundException,
) -> JSONResponse:
    """
    Handle room type not found exceptions.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=response.model_dump(),
    )
