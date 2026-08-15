from fastapi import Request, status
from fastapi.responses import JSONResponse
from jwt import (
    DecodeError,
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidAlgorithmError,
    InvalidAudienceError,
    InvalidIssuedAtError,
    InvalidIssuerError,
    InvalidKeyError,
    InvalidSignatureError,
    InvalidTokenError,
    MissingRequiredClaimError,
)

from booking.exceptions.definitions.security_exceptions import (
    UserUnauthorizedException,
)
from booking.schemas.common_schemas import ApiErrorResponse
from booking.types.error_codes import ErrorCodes


def user_unauthorized_exception_handler(
    _request: Request,
    exc: UserUnauthorizedException,
) -> JSONResponse:
    """
    Handle unauthorized access exceptions.

    Description
    -----------
    Generates a standardized API error response when a request fails
    authentication or authorization checks. This typically occurs when
    the user provides missing, expired, or invalid credentials and is
    not permitted to access the requested resource.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    exc : UserUnauthorizedException
        Exception containing authorization failure details, including
        the error code and user-facing message.

    Returns
    -------
    JSONResponse
        HTTP 401 Unauthorized response with a structured error payload
        describing the authentication or authorization failure.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=exc.errorCode,
        message=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=response.model_dump(),
    )


def expired_signature_error_exception_handler(
    _request: Request,
    _exc: ExpiredSignatureError,
) -> JSONResponse:
    """
    Handle JWT expired signature errors.

    Description
    -----------
    Generates a standardized API error response when the provided
    JWT access token has expired and is no longer valid for authentication.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    _exc : ExpiredSignatureError
        Exception raised when the JWT token has expired.

    Returns
    -------
    JSONResponse
        HTTP 401 Unauthorized response with a structured error payload
        indicating that the access token has expired.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=ErrorCodes.UNAUTHORIZED,
        message="Access token has expired. Please authenticate again.",
    )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=response.model_dump(),
    )


def invalid_token_error_exception_handler(
    _request: Request,
    _exc: InvalidTokenError,
) -> JSONResponse:
    """
    Handle invalid JWT token errors.

    Description
    -----------
    Generates a standardized API error response when the provided
    JWT access token is malformed, tampered with, or otherwise invalid.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    _exc : InvalidTokenError
        Exception raised when the JWT token is invalid.

    Returns
    -------
    JSONResponse
        HTTP 401 Unauthorized response with a structured error payload
        indicating that the access token is invalid.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=ErrorCodes.UNAUTHORIZED,
        message="Invalid access token. Please provide a valid token.",
    )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=response.model_dump(),
    )


def invalid_signature_error_exception_handler(
    _request: Request,
    _exc: InvalidSignatureError,
) -> JSONResponse:
    """
    Handle JWT invalid signature errors.

    Description
    -----------
    Generates a standardized API error response when the provided
    JWT access token has an invalid signature.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    _exc : InvalidSignatureError
        Exception raised when the JWT signature verification fails.

    Returns
    -------
    JSONResponse
        HTTP 401 Unauthorized response indicating an invalid token signature.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=ErrorCodes.UNAUTHORIZED,
        message="Invalid access token.",
    )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=response.model_dump(),
    )


def invalid_key_error_exception_handler(
    _request: Request,
    _exc: InvalidKeyError,
) -> JSONResponse:
    """
    Handle JWT invalid key errors.

    Description
    -----------
    Generates a standardized API error response when the signing
    or verification key used for JWT processing is invalid.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    _exc : InvalidKeyError
        Exception raised when the JWT key is invalid.

    Returns
    -------
    JSONResponse
        HTTP 401 Unauthorized response indicating token validation failure.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=ErrorCodes.UNAUTHORIZED,
        message="Invalid access token.",
    )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=response.model_dump(),
    )


def invalid_algorithm_error_exception_handler(
    _request: Request,
    _exc: InvalidAlgorithmError,
) -> JSONResponse:
    """
    Handle JWT invalid algorithm errors.

    Description
    -----------
    Generates a standardized API error response when the JWT
    algorithm used is not supported or allowed.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    _exc : InvalidAlgorithmError
        Exception raised when the JWT algorithm is invalid.

    Returns
    -------
    JSONResponse
        HTTP 401 Unauthorized response indicating invalid token algorithm.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=ErrorCodes.UNAUTHORIZED,
        message="Invalid access token.",
    )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=response.model_dump(),
    )


def invalid_audience_error_exception_handler(
    _request: Request,
    _exc: InvalidAudienceError,
) -> JSONResponse:
    """
    Handle JWT invalid audience errors.

    Description
    -----------
    Generates a standardized API error response when the JWT
    audience claim does not match the expected value.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    _exc : InvalidAudienceError
        Exception raised when the JWT audience is invalid.

    Returns
    -------
    JSONResponse
        HTTP 401 Unauthorized response indicating invalid token audience.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=ErrorCodes.UNAUTHORIZED,
        message="Invalid access token.",
    )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=response.model_dump(),
    )


def invalid_issuer_error_exception_handler(
    _request: Request,
    _exc: InvalidIssuerError,
) -> JSONResponse:
    """
    Handle JWT invalid issuer errors.

    Description
    -----------
    Generates a standardized API error response when the JWT
    issuer claim does not match the expected issuer.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    _exc : InvalidIssuerError
        Exception raised when the JWT issuer is invalid.

    Returns
    -------
    JSONResponse
        HTTP 401 Unauthorized response indicating invalid token issuer.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=ErrorCodes.UNAUTHORIZED,
        message="Invalid access token.",
    )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=response.model_dump(),
    )


def invalid_issued_at_error_exception_handler(
    _request: Request,
    _exc: InvalidIssuedAtError,
) -> JSONResponse:
    """
    Handle JWT invalid issued-at claim errors.

    Description
    -----------
    Generates a standardized API error response when the JWT
    issued-at (iat) claim is invalid.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    _exc : InvalidIssuedAtError
        Exception raised when the issued-at claim is invalid.

    Returns
    -------
    JSONResponse
        HTTP 401 Unauthorized response indicating invalid issued-at claim.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=ErrorCodes.UNAUTHORIZED,
        message="Invalid access token.",
    )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=response.model_dump(),
    )

def immature_signature_error_exception_handler(
    _request: Request,
    _exc: ImmatureSignatureError,
) -> JSONResponse:
    """
    Handle JWT immature signature errors.

    Description
    -----------
    Generates a standardized API error response when the JWT
    is used before its valid-from (nbf) time.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    _exc : ImmatureSignatureError
        Exception raised when the token is not yet valid.

    Returns
    -------
    JSONResponse
        HTTP 401 Unauthorized response indicating token is not yet active.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=ErrorCodes.UNAUTHORIZED,
        message="Access token is not yet valid.",
    )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=response.model_dump(),
    )


def missing_required_claim_error_exception_handler(
    _request: Request,
    _exc: MissingRequiredClaimError,
) -> JSONResponse:
    """
    Handle JWT missing required claim errors.

    Description
    -----------
    Generates a standardized API error response when the provided
    JWT access token is missing one or more required claims such as
    `exp`, `sub`, or `aud`.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    _exc : MissingRequiredClaimError
        Exception raised when a required JWT claim is missing.

    Returns
    -------
    JSONResponse
        HTTP 401 Unauthorized response indicating a malformed token.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=ErrorCodes.UNAUTHORIZED,
        message="Access token is missing required claims.",
    )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=response.model_dump(),
    )


def decode_error_exception_handler(
    _request: Request,
    _exc: DecodeError,
) -> JSONResponse:
    """
    Handle JWT decode errors.

    Description
    -----------
    Generates a standardized API error response when the provided
    JWT access token is malformed, corrupted, or cannot be decoded.

    Parameters
    ----------
    _request : Request
        The incoming FastAPI request object.
    _exc : DecodeError
        Exception raised when JWT decoding fails.

    Returns
    -------
    JSONResponse
        HTTP 401 Unauthorized response indicating an invalid token format.
    """

    response = ApiErrorResponse(
        metadata=None,
        errorCode=ErrorCodes.UNAUTHORIZED,
        message="Malformed access token.",
    )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=response.model_dump(),
    )
