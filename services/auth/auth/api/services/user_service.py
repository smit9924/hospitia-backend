import logging
import re
import uuid
from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from auth.api.repositories.user_repository import (
    add_otp,
    create_user,
    get_latest_unused_otp_for_user,
    get_user_by_guid,
    get_user_by_username,
    mark_otp_used_and_email_verified,
    mark_otps_as_used,
    update_user_data,
    update_user_password,
)
from auth.api.services.common_service import generate_otp, is_password_strong
from auth.api.services.login_service import authenticate_manual_user
from auth.core.config import settings
from auth.core.security import create_jwt_access_token, create_jwt_refresh_token
from auth.database.models.users import Users
from auth.exceptions.definitions.not_found_exceptions import (
    UserNotFoundException,
)
from auth.exceptions.definitions.security_exceptions import InvalidCredentialsException
from auth.exceptions.definitions.validation_exceptions import (
    EmailAlreadyVerifiedException,
    InvalidOtpException,
    InvalidUsernameException,
    UserWithUsernameAlreadyExistsException,
    WeakPasswordException,
)
from auth.messaging.general import get_mq_client
from auth.schemas.auth_schemas import JWTSubject, Token
from auth.schemas.mq_schemas import (
    MqDomainEvent,
    MqUserCreatedPayload,
    MqVerifyEmailOtpMessage,
)
from auth.schemas.user_schemas import ChangePassword, ProfileData, ProfileUpdate

VERIFY_EMAIL_OTP_LENGTH = 6
log = logging.getLogger(__name__)


def get_user_profile_data(*, session: Session, user_guid: str) -> ProfileData:
    """
    Retrieve the profile data for a user.

    parameters
    ----------
    session : Session
        Active SQLModel session for database operations.
    user_guid : str
        The GUID of the user whose profile data is to be retrieved.
    """
    log.info("Started")
    user = get_user_by_guid(session=session, guid=user_guid)
    if not user:
        log.warning("User not found guid=%s", user_guid)
        raise UserNotFoundException()

    log.info("Profile data retrieved guid=%s", user.guid)
    return ProfileData(
        guid=str(user.guid),
        email=user.email,
        role=user.role,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_email_verified=user.is_email_verified,
    )


def signupUser(*, session: Session, user: Users) -> Token:
    """
    Sign up a new user and create a JWT token for authentication.
    Publish a user created event to the message queue.

    parameters
    ----------
        session : Session
            Active SQLModel session for database operations.
        user : Users
            The user object containing the details of the user to be created.
    """
    log.info("Started")
    validated_user = user.model_validate(user)

    # Validate password streangth
    if not is_password_strong(validated_user.password):
        log.error("Weak password")
        raise WeakPasswordException()

    # Validate username format
    if not is_valid_username(validated_user.username):
        log.error("Invalid username")
        raise InvalidUsernameException()

    created_user = create_user(session=session, validated_user=validated_user)

    if created_user.id is None or created_user.guid is None:
        log.error("Persisted user without ID")
        raise UserNotFoundException("Persisted user without ID")

    event = MqDomainEvent(
        event_id=uuid.uuid4(),
        event_type=settings.USER_CREATED_EVENT_TYPE,
        occurred_at=datetime.now(UTC),
        payload=MqUserCreatedPayload(
            id=created_user.id,
            guid=created_user.guid,
            email=created_user.email,
            username=created_user.username,
            first_name=created_user.first_name,
            last_name=created_user.last_name,
        ).model_dump(mode="json"),
    )
    get_mq_client().publish(settings.USER_EVENTS_EXCHANGE, event, settings.USER_CREATED_ROUTING_KEY)
    log.info("User created event published event_id=%s guid=%s", event.event_id, created_user.guid)
    session.commit()

    access_token, access_token_expiry = create_jwt_access_token(
        subject=JWTSubject (
            user_guid=str(created_user.guid), # UUID is not JSON serializable, convert to string
            role=created_user.role,
        )
    )

    refresh_token, refresh_token_expiry = create_jwt_refresh_token(
        subject=JWTSubject (
            user_guid=str(created_user.guid), # UUID is not JSON serializable, convert to string
            role=created_user.role,
        )
    )

    log.info("User created successfully guid=%s", created_user.guid)
    return Token(
        access_token=access_token,
        access_token_expiry=access_token_expiry,
        refresh_token=refresh_token,
        refresh_token_expiry=refresh_token_expiry,
        token_type="bearer"
    )


def validate_username_uniqueness(*, session: Session, username: str) -> None:
    """
    Validate that the provided username is unique in the system.

    parameters
    ----------
        session : Session
            Active SQLModel session for database operations.
        username : str
            The username to be validated for uniqueness.
    raises
    -------
        UserWithUsernameAlreadyExistsException
            If a user with the provided username already exists in the system.
    """
    # Validate username format
    if not is_valid_username(username):
        raise InvalidUsernameException()

    user = get_user_by_username(session = session, username = username)

    if user is not None:
        raise UserWithUsernameAlreadyExistsException()


def is_valid_username(username: str | None) -> bool:
    """
    Validate the format of a username based on defined criteria.

    criteria for a valid username:
    -------------------------------
    - Must not be None.
    - Must not contain spaces.
    - Must start with a letter (a-z or A-Z).
    - Must end with a letter or digit (a-z, A-Z, or 0-9).
    - Can only contain letters (a-z, A-Z), digits (0-9), and underscores (_).

    parameters
    ----------
    username : str | None
        The username to be validated.

    returns
    -------
        bool : True if the username is valid, False otherwise.
    """
    if username is None:
        return False

    # Rule 1: no spaces
    if re.search(r"\s", username):
        return False

    # Rule 2: must start with a letter
    if not re.match(r"[a-zA-Z]", username):
        return False

    # Rule 3: must end with a letter or digit
    if not re.search(r"[a-zA-Z0-9]$", username):
        return False

    # Rule 4: allowed characters only
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False

    return True


def update_user_profile(*, session: Session, user_guid: str, profile_data: ProfileUpdate) -> ProfileData:
    """
    Update the profile data for a user.

    parameters
    ----------
    session : Session
        Active SQLModel session for database operations.
    user_guid : str
        The GUID of the user whose profile data is to be updated.
    profile_data : ProfileData
        The new profile data to be updated for the user.
    """
    log.info("Started")
    user = update_user_data(session=session, user_guid=user_guid, profile_data=profile_data)

    log.info("Profile updated guid=%s", user.guid)
    return ProfileData(
        guid=str(user.guid),
        email=user.email,
        role=user.role,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_email_verified=user.is_email_verified,
    )


def change_user_password(*, session: Session, user_guid: str, change_password_data: ChangePassword) -> None:
    log.info("Started")
    user = get_user_by_guid(session=session, guid=user_guid)

    if not user:
        log.warning("User not found guid=%s", user_guid)
        raise UserNotFoundException()

    authenticated_user = authenticate_manual_user(
        session=session,
        identifire=user.email,
        password=change_password_data.current_password,
    )

    if not authenticated_user:
        log.warning("Invalid current password guid=%s", user_guid)
        raise InvalidCredentialsException()

    # Validate password streangth
    if not is_password_strong(change_password_data.new_password):
        log.warning("Weak password guid=%s", user_guid)
        raise WeakPasswordException()

    update_user_password(session=session, user_id=user.id, new_password=change_password_data.new_password)
    log.info("Password changed guid=%s", user_guid)


def request_email_verification_otp(*, session: Session, user_guid: str) -> dict[str, str]:
    """
    Generate and email an OTP for verifying the authenticated user's email.
    """
    log.info("Started")
    user = get_user_by_guid(session=session, guid=user_guid)
    if not user:
        log.warning("User not found guid=%s", user_guid)
        raise UserNotFoundException()

    if user.is_email_verified:
        log.warning("Email already verified guid=%s", user_guid)
        raise EmailAlreadyVerifiedException()

    if user.id is None:
        raise UserNotFoundException("Persisted user without ID")

    mark_otps_as_used(session=session, user_id=user.id)

    otp_value = generate_otp(VERIFY_EMAIL_OTP_LENGTH)
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.VERIFY_EMAIL_OTP_TIMEOUT)
    add_otp(session=session, user_id=user.id, otp=otp_value, expires_at=expires_at)

    message = MqVerifyEmailOtpMessage(
        to=[user.email],
        subject="Verify Your Email",
        user_first_name=user.first_name if user.first_name else "",
        user_last_name=user.last_name if user.last_name else "",
        otp=otp_value,
        expiration_time=settings.VERIFY_EMAIL_OTP_TIMEOUT,
    )

    mq_client = get_mq_client()
    mq_client.publish(settings.VERIFY_EMAIL_OTP_EMAIL_QUEUE, message)
    log.info("Email verification OTP queued guid=%s", user.guid)

    return {"message": "A verification OTP has been sent to your email"}


def verify_email_otp(*, session: Session, user_guid: str, otp: str) -> dict[str, str]:
    """
    Validate an email verification OTP and mark the user's email as verified.
    """
    log.info("Started")
    user = get_user_by_guid(session=session, guid=user_guid)
    if not user:
        log.warning("User not found guid=%s", user_guid)
        raise UserNotFoundException()

    if user.is_email_verified:
        log.warning("Email already verified guid=%s", user_guid)
        raise EmailAlreadyVerifiedException()

    if user.id is None:
        raise UserNotFoundException("Persisted user without ID")

    otp_record = get_latest_unused_otp_for_user(session=session, user_id=user.id)
    now = datetime.now(UTC)

    if otp_record is None:
        log.warning("Invalid OTP guid=%s", user_guid)
        raise InvalidOtpException()

    expires_at = otp_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if otp_record.used or expires_at <= now or otp_record.otp != otp:
        log.warning("Invalid OTP guid=%s", user_guid)
        raise InvalidOtpException()

    mark_otp_used_and_email_verified(
        session=session,
        otp_record=otp_record,
        user=user,
    )

    log.info("Email verified guid=%s", user.guid)
    return {"message": "Email verified successfully"}
