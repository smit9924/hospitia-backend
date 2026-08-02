import logging
from datetime import UTC, datetime

from pydantic import AnyHttpUrl, TypeAdapter
from sqlmodel import Session, select

from auth.api.dependencies import SessionDep
from auth.api.repositories.user_repository import (
    add_security_token,
    get_user_by_email_or_username,
    mark_security_tokens_as_used,
)
from auth.core.config import settings
from auth.core.security import (
    create_jwt_access_token,
    create_jwt_refresh_token,
    generate_secure_token,
    get_password_hash,
    hash_secure_token,
    verify_password,
)
from auth.database.models.security import SecureToken
from auth.database.models.users import Users
from auth.exceptions.definitions.not_found_exceptions import UserNotFoundException
from auth.exceptions.definitions.security_exceptions import (
    InvalidCredentialsException,
    UserInactiveException,
)
from auth.messaging.general import get_mq_client
from auth.schemas.auth_schemas import (
    JWTSubject,
    Token,
)
from auth.schemas.common_schemas import ApiErrorResponse, ErrorCodes
from auth.schemas.mq_schemas import MqForgotPasswordMessage
from auth.types.enums import AuthType

log = logging.getLogger(__name__)

def login(*, session: SessionDep, username: str, password: str, remember_me: bool = False) -> Token:
    """
    Authenticate a user and issue an OAuth2 access token.

    Validates the provided username/email and password using the OAuth2
    password grant flow. If authentication is successful, a JWT access
    token is generated and returned for use in subsequent authenticated
    requests.
    """
    authenticated_user = authenticate_manual_user(
        session=session,
        identifire=username,
        password=password,
    )

    if not authenticated_user:
        raise InvalidCredentialsException()
    elif not authenticated_user.is_active:
        raise UserInactiveException()

    access_token, access_token_expiry = create_jwt_access_token(
        subject=JWTSubject (
            user_guid=str(authenticated_user.guid), # UUID is not JSON serializable, convert to string
            role=authenticated_user.role,
        )
    )

    refresh_token, refresh_token_expiry = create_jwt_refresh_token(
        subject=JWTSubject (
            user_guid=str(authenticated_user.guid), # UUID is not JSON serializable, convert to string
            role=authenticated_user.role,
        ),
        remember_me=remember_me,
    )

    return Token(
        access_token=access_token,
        access_token_expiry=access_token_expiry,
        refresh_token=refresh_token,
        refresh_token_expiry=refresh_token_expiry,
        token_type="bearer"
    )

def authenticate_manual_user(*, session: Session, identifire: str, password: str) -> Users | None:
    """
    Authenticate a user using manual authentication.

    Verifies the provided email/username and password against the database.
    Only users registered with MANUAL authentication are eligible.
    Returns the user object if authentication succeeds; otherwise, returns None.

    parameters
    ----------
        session : Session
            Active SQLModel session for database operations.
        email_or_username : str
            The email address or username of the user attempting to log in.
        password : str
            The plain text password provided by the user for authentication.

    Returns
    -------
    Users | None
        The authenticated user instance if the credentials are valid;
        otherwise, ``None``.
    """
    user = get_user_by_email_or_username(session=session, identifire=identifire)

    if not user:
        return None

    if not user.auth_type == AuthType.MANUAL:
        return None

    if (not user.password) or (not verify_password(plain_password=password, hashed_password=user.password)):
        return None

    return user

def forgot_password_user(*, session: Session, email: str) -> None:
    """
    Handle forgot password requests.

    Validates the provided email address and, if a user with that email exists,
    initiates the password reset process (e.g., by sending a reset link via email).
    Returns a message indicating that the reset link has been sent, without
    revealing whether the email is associated with an account for security reasons.

    parameters
    ----------
        session : Session
            Active SQLModel session for database operations.
        email : str
            The email address of the user requesting a password reset.

    """
    user = get_user_by_email_or_username(session=session, identifire=email)

    if not user:
        # For security, do not reveal whether the email exists in the system
        return

    if(user.id is None):
            raise UserNotFoundException("Persisted user without ID")

    # invalidate old tokens
    mark_security_tokens_as_used(session=session, user_id=user.id)

    token, expire_time = generate_secure_token()
    hash_token = hash_secure_token(token)
    add_security_token(session=session, user_id=user.id, token=hash_token, expires_at=expire_time)


    reset_link: AnyHttpUrl = TypeAdapter(AnyHttpUrl).validate_python(f"{settings.FRONTEND_BASE_URL}/reset-password?token={token}")

    message = MqForgotPasswordMessage(
        to=[email],
        subject="Password Reset Link",
        user_first_name=user.first_name if user.first_name else "",
        user_last_name=user.last_name if user.last_name else "",
        reset_password_link=reset_link,
        expiration_time=settings.RESET_TOKEN_EXPIRE_MINUTES
    )

    mq_client = get_mq_client()
    mq_client.publish(settings.FORGOT_PASSWORD_EMAIL_QUEUE, message)

def reset_password_user(*, session: Session, reset_token: str, new_password: str) -> None:
    """
    Handle password reset requests.

    Validates the provided reset token and, if valid, updates the user's password
    in the database. Returns a message indicating that the password has been reset,
    without revealing whether the token is valid for security reasons.

    parameters
    ----------
        session : Session
            Active SQLModel session for database operations.
        token : str
            The password reset token provided by the user.
        new_password : str
            The new plain text password that the user wants to set.
    """
    token_hash = hash_secure_token(reset_token)
    now = datetime.now(UTC)

    # atomically consume token
    stmt = (
        select(SecureToken)
        .where(SecureToken.token == token_hash)
        .with_for_update()
    )

    record = session.exec(stmt).first()

    if record is None:
        return

    if record.used or record.expires_at <= now:
        ApiErrorResponse(
            metadata=None,
            message="Invalid or expired token",
            errorCode=ErrorCodes.INVALIDTOKEN
        )

    user = session.get(Users, record.user_id)
    if user is None:
        return

    user.password = get_password_hash(new_password)
    record.used = True

    session.add(user)
    session.add(record)
    session.commit()

