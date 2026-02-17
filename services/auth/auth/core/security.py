from datetime import UTC, datetime

from bcrypt import checkpw, gensalt, hashpw
from jwt import InvalidTokenError, decode, encode
from sqlmodel import Session, select

from auth.core.config import settings
from auth.database.models import Users
from auth.exceptions.definitions.security_exceptions import UserUnauthorizedException
from auth.schemas.auth_schemas import (
    JWTPayload,
    JWTSubject,
    ParsedJWTPayload,
    TokenType,
)
from auth.types.enums import UserType


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
    return jwt_token

def create_jwt_refresh_token(*, subject: JWTSubject) -> str:
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
    expire = datetime.now(UTC) + settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS_TIMEDELTA

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
    ParsedJWTAccessTokenPayload
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
) -> None:
    """
    Authorize the authenticated user based on allowed roles.

    Description
    -----------
    Validates that the user associated with the JWT payload exists in the
    database and has a role included in the allowed roles list. If `roles`
    is None, authorization is skipped and access is granted to all users.

    Parameters
    ----------
    token_payload : ParsedJWTAccessTokenPayload
        Parsed JWT payload containing authenticated user details.
    session : Session
        Database session used to fetch user information.
    roles : list[UserType] | None, optional
        List of roles allowed to access the resource. If None, access is
        allowed for all authenticated users.

    Returns
    -------
    None

    Raises
    ------
    UserUnauthorizedException
        If the user does not exist or does not have a permitted role.
    """

    stmt = select(Users).where(
        Users.guid == token_payload.parsed_subject.user_guid
    )
    user = session.exec(stmt).first()

    if not user or user.role not in roles:
        raise UserUnauthorizedException

