from fastapi import Request, status
from fastapi.responses import JSONResponse

from dashboard.exceptions.definitions.messaging_queue_exceptions import (
    MQMessagePublishException,
    MQNotFoundException,
)
from dashboard.schemas.common_schemas import ApiErrorResponse


def mq_not_found_exception_handler(
    _request: Request,
    exc: MQNotFoundException,
) -> JSONResponse:
    """
    Handle messaging queue not found exceptions.

    Description
    -----------
    Generates a standardized API error response when a requested messaging queue
    cannot be found.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    exc : MQNotFoundException
        Exception containing details about the messaging queue not found error, including
        the error code and user-facing message.

    Returns
    -------
    JSONResponse
        HTTP 404 Not Found response with a structured error payload describing
        the missing messaging queue.
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


def mq_message_publish_exception_handler(
    _request: Request,
    exc: MQMessagePublishException,
) -> JSONResponse:
    """
    Handle messaging queue message publish exceptions.

    Description
    -----------
    Generates a standardized API error response when a message cannot be published
    to the messaging queue.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    exc : MQMessagePublishException
        Exception containing details about the message publish failure, including
        the error code and user-facing message.

    Returns
    -------
    JSONResponse
        HTTP 500 Internal Server Error response with a structured error payload describing
        the message publish failure.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(),
    )
