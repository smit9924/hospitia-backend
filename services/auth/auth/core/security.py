import json
from datetime import UTC, datetime
from typing import Any

from bcrypt import checkpw, gensalt, hashpw
from jwt import decode, encode, InvalidTokenError


from auth.core.config import settings
from auth.schemas.auth_schemas import JWTAccessTokenPayload, JWTSubject, ParsedJWTAccessTokenPayload
from auth.exceptions.definitions.security_exceptions import UserUnauthorizedException


def create_jwt_access_token(*, subject: JWTSubject) -> str:
    """
    Create a JSON Web Token (JWT) access token for a given subject.

    Description
    -----------
        Build and encode a JWT containing the subject and an expiration
        claim using the application's JWT settings.

    Parameters
    ----------
        subject (dict | None) : Optional dictionary of subject claims (e.g., {"user_id": 123} or {"email": "user@example.com"}).

    Returns:
        str -- Encoded JWT access token as a string.
    """
    expire = datetime.now(UTC) + settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES_TIMEDELTA

    to_encode = JWTAccessTokenPayload(
        exp=expire,
        sub=subject.model_dump_json() # Convert subject to a string since non-string values cause token validation failures
    )

    jwt_token = encode(
        payload=to_encode.model_dump(),
        key=settings.JWT_ENCRYPTION_SECRET_KEY,
        algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
    )
    return jwt_token


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Validates a plaintext password against a bcrypt-hashed password.

    Parameters
    ----------
    plain_password : str
        The plaintext password to validate.

    hashed_password : str
        The bcrypt-hashed password to validate against.

    Returns
    -------
    bool
        True if the plaintext password matches the hashed password, otherwise False.
    """
    return checkpw(
        bytes(plain_password, encoding="utf-8"),
        bytes(hashed_password, encoding="utf-8"),
    )


def get_password_hash(password: str) -> str:
    """
    Create a bcrypt hash from the given plaintext password.

    Parameters
    ----------
    password : str
        The plaintext password to hash.

    Returns
    -------
    str
        The bcrypt-hashed password as a UTF-8 decoded string (includes salt).
    """
    password_hash_byte = hashpw(
        bytes(password, encoding="utf-8"),
        gensalt(),
    )

    password_hash_string = password_hash_byte.decode("utf-8")

    return password_hash_string


def decode_jwt_token(token: str) -> ParsedJWTAccessTokenPayload:
    try:
        payload: dict = decode(
            jwt=token,
            key=settings.JWT_ENCRYPTION_SECRET_KEY,
            algorithms=[settings.JWT_ENCRYPTION_ALGORITHM],
        )

        subject = JWTSubject.model_validate_json(payload["sub"])

        return ParsedJWTAccessTokenPayload(
            exp=payload["exp"],
            sub=payload["sub"],
            parsed_subject=subject,
        )

    # Propagate all PyJWT validation errors unchanged.
    # InvalidTokenError is the base class for all JWT-related exceptions.
    except InvalidTokenError:
        raise

    # Mask any unexpected error as a generic authentication failure
    # to avoid leaking internal implementation details.
    except Exception:
        raise UserUnauthorizedException

