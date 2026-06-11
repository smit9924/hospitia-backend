from typing import Any

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

from auth.exceptions.definitions.not_found_exceptions import (
    UserNotFoundException,
)
from auth.exceptions.definitions.security_exceptions import (
    InvalidCredentialsException,
    UserInactiveException,
    UserUnauthorizedException,
)
from auth.exceptions.definitions.validation_exceptions import (
    InvalidUsernameException,
    PublicEmailNotAllowedException,
    UserWithEmailAlreadyExistsException,
    UserWithUsernameAlreadyExistsException,
    WeakPasswordException,
)
from auth.exceptions.handlers.not_found_exceptions_handlers import (
    user_not_found_exception_handler,
)
from auth.exceptions.handlers.security_exceptions_handlers import (
    decode_error_exception_handler,
    expired_signature_error_exception_handler,
    immature_signature_error_exception_handler,
    inactive_user_exception_handler,
    invalid_algorithm_error_exception_handler,
    invalid_audience_error_exception_handler,
    invalid_credentials_exception_handler,
    invalid_issued_at_error_exception_handler,
    invalid_issuer_error_exception_handler,
    invalid_key_error_exception_handler,
    invalid_signature_error_exception_handler,
    invalid_token_error_exception_handler,
    missing_required_claim_error_exception_handler,
    user_unauthorized_exception_handler,
)
from auth.exceptions.handlers.validation_exception_handlers import (
    invalid_username_exception_handler,
    public_email_not_allowed_exception_handler,
    user_with_email_already_exists_exception_handler,
    user_with_username_already_exists_exception_handler,
    weak_password_exception_handler,
)


def get_exception_handlers() -> dict[Any, Any]:
    """
    Returns a mapping of custom exception types to their corresponding
    FastAPI exception handler callables.
    """
    return {
        # Register VALIDATION EXCEPTION handlers
        PublicEmailNotAllowedException: public_email_not_allowed_exception_handler,
        UserWithEmailAlreadyExistsException: user_with_email_already_exists_exception_handler,
        UserWithUsernameAlreadyExistsException: user_with_username_already_exists_exception_handler,
        WeakPasswordException: weak_password_exception_handler,
        InvalidUsernameException: invalid_username_exception_handler,

        # Register CUSTOM SECURITY EXCEPTION handlers
        UserUnauthorizedException: user_unauthorized_exception_handler,
        InvalidCredentialsException: invalid_credentials_exception_handler,
        UserInactiveException: inactive_user_exception_handler,

        # Register PYJWT SECURITY EXCEPTION handlers
        ExpiredSignatureError: expired_signature_error_exception_handler,
        InvalidTokenError: invalid_token_error_exception_handler,
        InvalidSignatureError: invalid_signature_error_exception_handler,
        InvalidKeyError: invalid_key_error_exception_handler,
        InvalidAlgorithmError: invalid_algorithm_error_exception_handler,
        InvalidAudienceError: invalid_audience_error_exception_handler,
        InvalidIssuerError: invalid_issuer_error_exception_handler,
        InvalidIssuedAtError: invalid_issued_at_error_exception_handler,
        ImmatureSignatureError: immature_signature_error_exception_handler,
        MissingRequiredClaimError: missing_required_claim_error_exception_handler,
        DecodeError: decode_error_exception_handler,

        # Register NOT FOUND EXCEPTION handlers
        UserNotFoundException: user_not_found_exception_handler,
    }
