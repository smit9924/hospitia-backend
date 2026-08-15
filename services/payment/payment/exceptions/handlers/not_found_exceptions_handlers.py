from fastapi import Request, status
from fastapi.responses import JSONResponse

from payment.exceptions.definitions.not_found_exceptions import (
    UserNotFoundException,
)
from payment.schemas.common_schemas import ApiErrorResponse


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
