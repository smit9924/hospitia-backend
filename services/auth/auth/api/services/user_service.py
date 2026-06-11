import re

from sqlmodel import Session

from auth.api.repositories.user_repository import (
    create_user,
    get_user_by_guid,
    get_user_by_username,
    update_user_data,
)
from auth.core.security import create_jwt_access_token, create_jwt_refresh_token
from auth.database.models.users import Users
from auth.exceptions.definitions.not_found_exceptions import (
    UserNotFoundException,
)
from auth.exceptions.definitions.validation_exceptions import (
    InvalidUsernameException,
    UserWithUsernameAlreadyExistsException,
    WeakPasswordException,
)
from auth.schemas.auth_schemas import JWTSubject, Token
from auth.schemas.user_schemas import ProfileData, ProfileUpdate


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
    validated_user = user.model_validate(user)

    # Validate password streangth
    if not is_password_strong(validated_user.password):
        raise WeakPasswordException()

    # Validate username format
    if not is_valid_username(validated_user.username):
        raise InvalidUsernameException()

    created_user = create_user(session=session, validated_user=validated_user)

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

def is_password_strong(password: str | None) -> bool:
    r"""
    Validate the strength of a password based on defined criteria.

    criteria for a strong password:
    -------------------------------
    - Minimum length of 8 characters and maximum length of 50 characters.
    - Contains at least one uppercase letter.
    - Contains at least one lowercase letter.
    - Contains at least one digit.
    - Contains at least one special character (e.g., !@#$%^&*(),.?":{}|<>_-[];'\/+=~`).

    parameters
    ----------
        password : str | None

    returns
    -------
        bool : True if the password is strong, False otherwise.

    """
    if ( password is None
        or len(password) < 8
        or len(password) > 50
        or not re.search(r"[A-Z]", password)
        or not re.search(r"[a-z]", password)
        or not re.search(r"\d", password)
        or not re.search(r"[!@#$%^&*(),.?\":{}|<>\_\-\[\];'/+=~`]", password)
    ):
        return False

    return True

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

    user = update_user_data(session=session, user_guid=user_guid, profile_data=profile_data)

    return ProfileData(
        guid=str(user.guid),
        email=user.email,
        role=user.role,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
