
from jwt import InvalidTokenError, decode

from payment.core.config import settings
from payment.exceptions.definitions.security_exceptions import UserUnauthorizedException
from payment.schemas.auth_schemas import (
    JWTSubject,
    ParsedJWTPayload,
    TokenType,
)


def decode_jwt_token(token: str, expected_type: TokenType) -> ParsedJWTPayload:
    """
    Decode and validate a JWT access token.

    Description
    -----------
    Decodes the provided JWT access token using the configured encryption
    key and algorithm, validates its claims, and converts the subject (`sub`)
    claim into a strongly-typed schema.

    Parameters
    ----------
    token : str
        The encoded JWT access token.

    Returns
    -------
    ParsedJWTPayload
        A validated JWT payload containing the token expiration time,
        raw subject claim, and a parsed subject model.

    Raises
    ------
    InvalidTokenError
        If the JWT is invalid, expired, malformed, or fails signature
        verification. All PyJWT validation errors are propagated unchanged.

    UserUnauthorizedException
        If any unexpected error occurs during token decoding or payload
        parsing, indicating an authentication failure.
    """
    try:
        payload: dict = decode(
            jwt=token,
            key=settings.JWT_ENCRYPTION_SECRET_KEY,
            algorithms=[settings.JWT_ENCRYPTION_ALGORITHM],
        )

        if TokenType(payload["type"]) != expected_type:
            raise UserUnauthorizedException

        subject = JWTSubject.model_validate_json(payload["sub"])

        return ParsedJWTPayload(
            exp=payload["exp"],
            sub=payload["sub"],
            parsed_subject=subject,
            type=payload["type"]
        )

    # Propagate all PyJWT validation errors unchanged.
    # InvalidTokenError is the base class for all JWT-related exceptions.
    except InvalidTokenError:
        raise

    # Mask any unexpected error as a generic authentication failure
    # to avoid leaking internal implementation details.
    except Exception:
        raise UserUnauthorizedException
