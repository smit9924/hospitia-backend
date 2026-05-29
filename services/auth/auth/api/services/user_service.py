from sqlmodel import Session

from auth.api.repositories.user_repository import (
    get_user_by_guid,
    get_user_by_username,
    validate_and_create_user,
)
from auth.core.security import create_jwt_access_token, create_jwt_refresh_token
from auth.database.models.users import Users
from auth.exceptions.definitions.not_found_exceptions import (
    UserNotFoundException,
)
from auth.exceptions.definitions.validation_exceptions import (
    UserWithUsernameAlreadyExistsException,
)
from auth.schemas.auth_schemas import JWTSubject, Token
from auth.schemas.user_schemas import ProfileData


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
    # Implementation for fetching user profile data
    user = get_user_by_guid(session=session, guid=user_guid)
    if not user:
        raise UserNotFoundException()

    return ProfileData(
        guid=str(user.guid),
        email=user.email,
        role=user.role,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

def signupUser(*, session: Session, user: Users) -> Token:
    """
    Sign up a new user and create a JWT token for authentication.

    parameters
    ----------
        session : Session
            Active SQLModel session for database operations.
        user : Users
            The user object containing the details of the user to be created.
    """
    created_user = validate_and_create_user(session=session, user=user)

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
    user = get_user_by_username(session = session, username = username)

    if user is not None:
        raise UserWithUsernameAlreadyExistsException()
