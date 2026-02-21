from datetime import UTC, datetime
import json
from turtle import reset
from auth.database.models.secure_token import SecureToken
from auth.messaging.publisher import publish_message
import pika
from auth.messaging.connection import create_connection
from sqlmodel import Session, select, update, update

from auth.api.services.user_service import get_password_hash, get_user_by_email_or_username
from auth.core.security import generate_secure_token, hash_secure_token, settings, verify_password
from auth.database.models.users import Users
from auth.types.enums import AuthType
import logging

log = logging.getLogger(__name__)

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

    Returns
    -------
    dict
        A message indicating that a reset link has been sent to the provided email address.
    """
    user = get_user_by_email_or_username(session=session, identifire=email)

    if not user:
        # For security, do not reveal whether the email exists in the system
        return
    
    token, expire_time = generate_secure_token()

    if(user.id is None):
            raise RuntimeError("Persisted user without ID")


    hash_token = hash_secure_token(token)

    # invalidate old tokens
    stmt = select(SecureToken).where(
        SecureToken.user_id == user.id,
        SecureToken.used == False
    )
    
    for record in session.exec(stmt):
        record.used = True

    reset_token = SecureToken(
        user_id=user.id,
        token=hash_token,
        expires_at=expire_time,
    )

    session.add(reset_token)
    session.commit()

    reset_link = f"{settings.FRONTEND_BASE_URL}/reset-password?token={token}"
    
    message = {
        "channel": "email",
        "priority": 5,
        "payload": {
            "to": [email],
            "subject": "Password Reset Link",
            "template": "password_reset",
            "data": {
                "username": user.username,
                "reset_link": reset_link,
                "expires_in": settings.RESET_TOKEN_EXPIRE_MINUTES,
            }
        }
    }

    publish_message(message)

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
    Returns
    -------
    dict
        A message indicating that the password has been reset successfully.
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
        return

    user = session.get(Users, record.user_id)
    if user is None:
        return

    user.password = get_password_hash(new_password)
    record.used = True

    log.info(f"Resetting password for user_id={user.id} using token_id={record.id}")

    session.add(user)
    session.add(record)
    session.commit()

    log.info(f"Password reset successful for user_id={user.id} using token_id={record.id}") 

