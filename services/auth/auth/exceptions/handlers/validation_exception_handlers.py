from fastapi import Request, status
from fastapi.responses import JSONResponse

from auth.exceptions.definitions.validation_exceptions import (
    EmailAlreadyVerifiedException,
    InvalidOtpException,
    InvalidUsernameException,
    PublicEmailNotAllowedException,
    UserWithEmailAlreadyExistsException,
    UserWithUsernameAlreadyExistsException,
    WeakPasswordException,
)
from auth.schemas.common_schemas import ApiErrorResponse
from auth.schemas.exception_data_schemas import PublicEmailNotAllowedExceptionMetadata


def  public_email_not_allowed_exception_handler(_request: Request, exc: PublicEmailNotAllowedException) -> JSONResponse:
    """
    Handle the exception raised when a public email domain is used where a
    business or organization email address is required.

    Description
    -----------
        Generates a standardized API error response when a request fails
        due to the use of a disallowed public email domain, enforcing
        application-specific email domain policies.

    Parameters
    ----------
        request : Request
            The incoming FastAPI request object.
        exc : PublicEmailNotAllowedException
            Exception containing the validation error message.

    Returns
    -------
        JSONResponse
            HTTP 409 Conflict response with a structured error payload
            describing the business rule violation.
    """

    response = ApiErrorResponse (
        metadata = PublicEmailNotAllowedExceptionMetadata(
            input=exc.input,
            field=exc.field,
            data=exc.data,
        ),
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(),
    )

def  user_with_email_already_exists_exception_handler(_request: Request, exc: UserWithEmailAlreadyExistsException) -> JSONResponse:
    """
    Handle the exception raised when a user already exists with the given
    email address.

    Description
    -----------
        Generate a standardized API error response when a user registration
        attempt fails because the provided email address is
        already registered in the system.

    Parameters
    ----------
        _request : Request
            The incoming FastAPI request object.
        exc : UserWithEmailOrUsernameAlreadyExistsException
            Exception containing the conflict error message.

    Returns
    -------
        JSONResponse
            HTTP 409 Conflict response with a structured error payload
            describing the duplicate resource violation.
    """

    response = ApiErrorResponse (
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(),
    )

def  user_with_username_already_exists_exception_handler(_request: Request, exc: UserWithUsernameAlreadyExistsException) -> JSONResponse:
    """
    Handle the exception raised when a user already exists with the given
    email address.

    Description
    -----------
        Generate a standardized API error response when a user registration
        attempt fails because the provided email address is
        already registered in the system.

    Parameters
    ----------
        _request : Request
            The incoming FastAPI request object.
        exc : UserWithEmailOrUsernameAlreadyExistsException
            Exception containing the conflict error message.

    Returns
    -------
        JSONResponse
            HTTP 409 Conflict response with a structured error payload
            describing the duplicate resource violation.
    """

    response = ApiErrorResponse (
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(),
    )

def  weak_password_exception_handler(_request: Request, exc: WeakPasswordException) -> JSONResponse:
    """
    Handle the exception raised when a user provides a weak password.

    Description
    -----------
        Generate a standardized API error response when a user registration
        attempt fails because the provided password does not meet the required
        strength criteria.

    Parameters
    ----------
        _request : Request
            The incoming FastAPI request object.
        exc : WeakPasswordException
            Exception containing the conflict error message.

    Returns
    -------
        JSONResponse
            HTTP 409 Conflict response with a structured error payload
            describing the duplicate resource violation.
    """

    response = ApiErrorResponse (
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(),
    )


def  invalid_username_exception_handler(_request: Request, exc: InvalidUsernameException) -> JSONResponse:
    """
    Handle the exception raised when a user provides an invalid username.

    Description
    -----------
        Generate a standardized API error response when a user registration
        attempt fails because the provided username is invalid.

    Parameters
    ----------
        _request : Request
            The incoming FastAPI request object.
        exc : InvalidUsernameException
            Exception containing the conflict error message.

    Returns
    -------
        JSONResponse
            HTTP 409 Conflict response with a structured error payload
            describing the duplicate resource violation.
    """

    response = ApiErrorResponse (
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(),
    )


def email_already_verified_exception_handler(
    _request: Request,
    exc: EmailAlreadyVerifiedException,
) -> JSONResponse:
    """
    Handle the exception raised when email is already verified.
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


def invalid_otp_exception_handler(
    _request: Request,
    exc: InvalidOtpException,
) -> JSONResponse:
    """
    Handle the exception raised when an OTP is invalid or expired.
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
