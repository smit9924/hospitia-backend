import secrets
from datetime import UTC, datetime

from bcrypt import checkpw, gensalt, hashpw
from jwt import InvalidTokenError, decode, encode
from sqlmodel import Session, select

from auth.core.config import settings, timedelta
from auth.database.models import Users
from auth.exceptions.definitions.security_exceptions import UserUnauthorizedException
from auth.schemas.auth_schemas import (
    JWTPayload,
    JWTSubject,
    ParsedJWTPayload,
    TokenType,
)
from auth.types.enums import UserType


def create_jwt_access_token(*, subject: JWTSubject) -> tuple[str, datetime]:
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

    to_encode = JWTPayload(
        exp=expire,
        type=TokenType.ACCESS,
        sub=subject.model_dump_json() # Convert subject to a string since non-string values cause token validation failures
    )

    jwt_token = encode(
        payload=to_encode.model_dump(),
        key=settings.JWT_ENCRYPTION_SECRET_KEY,
        algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
    )
    return jwt_token, expire

def create_jwt_refresh_token(*, subject: JWTSubject, remember_me: bool = False) -> tuple[str, datetime]:
    """
    Create a JSON Web Token (JWT) refresh token for a given subject.

    Description
    -----------
        Build and encode a JWT containing the subject and an expiration
        claim using the application's JWT settings.

    Parameters
    ----------
        subject (dict | None) : Optional dictionary of subject claims (e.g., {"user_id": 123} or {"email": "user@example.com"}).

    Returns
        -------
        str
            Encoded JWT refresh token.

    """
    expire = datetime.now(UTC) + settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES_TIMEDELTA
    if remember_me:
        expire = datetime.now(UTC) + settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES_REMEMBER_ME_TIMEDELTA

    to_encode = JWTPayload(
        exp=expire,
        type=TokenType.REFRESH,
        sub=subject.model_dump_json() # Convert subject to a string since non-string values cause token validation failures
    )

    jwt_token = encode(
        payload=to_encode.model_dump(),
        key=settings.JWT_ENCRYPTION_SECRET_KEY,
        algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
    )
    return jwt_token, expire


def verify_hash(plain_value: str, hashed_value: str) -> bool:
    """
    Validates a plaintext value against a bcrypt hash.

    Used for passwords, secure tokens, and other secrets stored with bcrypt.

    Parameters
    ----------
    plain_value : str
        The plaintext value to validate.

    hashed_value : str
        The bcrypt-hashed value to validate against.

    Returns
    -------
    bool
        True if the plaintext value matches the hash, otherwise False.
    """
    return checkpw(
        bytes(plain_value, encoding="utf-8"),
        bytes(hashed_value, encoding="utf-8"),
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


def authorize_user(
    token_payload: ParsedJWTPayload,
    session: Session,
    roles: list[UserType],
    require_email_verified: bool = True,
) -> None:
    """
    Authorize the authenticated user based on allowed roles.

    Description
    -----------
    Validates that the user associated with the JWT payload exists in the
    database and has a role included in the allowed roles list. If
    ``require_email_verified`` is True, the user's email must also be verified.

    Parameters
    ----------
    token_payload : ParsedJWTAccessTokenPayload
        Parsed JWT payload containing authenticated user details.
    session : Session
        Database session used to fetch user information.
    roles : list[UserType] | None, optional
        List of roles allowed to access the resource. If None, access is
        allowed for all authenticated users.
    require_email_verified : bool
        When True, reject users whose email has not been verified.

    Returns
    -------
    None

    Raises
    ------
    UserUnauthorizedException
        If the user does not exist, does not have a permitted role, or has
        not verified their email when verification is required.
    """

    stmt = select(Users).where(
        Users.guid == token_payload.parsed_subject.user_guid
    )
    user = session.exec(stmt).first()

    if not user or user.role not in roles:
        raise UserUnauthorizedException()

    if require_email_verified and not user.is_email_verified:
        raise UserUnauthorizedException()

def generate_secure_token() -> tuple[str, datetime]:
    """
    Generate a secure random token for password reset or similar purposes.

    Returns
    -------
    tuple[str, datetime]
        A tuple containing the securely generated random token and its expiration time.
    """
    reset_token = secrets.token_urlsafe(48)
    expire_time = datetime.now(UTC) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    return reset_token, expire_time

def hash_secure_token(token: str) -> str:
    """
    Hash a secure token using bcrypt.

    Parameters
    ----------
    token : str
        The plaintext token to hash.

    Returns
    -------
    str
        The bcrypt-hashed token as a UTF-8 decoded string (includes salt).
    """
    token_hash_byte = hashpw(
        bytes(token, encoding="utf-8"),
        gensalt(),
    )

    token_hash_string = token_hash_byte.decode("utf-8")

    return token_hash_string
