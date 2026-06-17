from pydantic import EmailStr
from sqlmodel import Session, select

from auth.core.security import get_password_hash
from auth.database.models.users import Users
from auth.exceptions.definitions.not_found_exceptions import (
    UserNotFoundException,
)
from auth.exceptions.definitions.validation_exceptions import (
    UserWithEmailAlreadyExistsException,
    UserWithUsernameAlreadyExistsException,
)
from auth.schemas.user_schemas import ProfileUpdate


def get_user_by_guid(*, session: Session, guid: str) -> Users | None:
    """
    Retrieve a user by their GUID.

    Query the database for a user matching the provided GUID.
    Returns the user object if found, otherwise None.

    parameters
    ----------
        session : Session
            Active SQLModel session for database operations.
        guid : str
            The GUID to search for.
    """
    get_user_by_guid_statement = select(Users).where(
        Users.guid == guid
    )
    user = session.exec(get_user_by_guid_statement).first()
    return user


def get_user_by_id(*, session: Session, id: int | None) -> Users | None:
    """
    Retrieve a user by their ID.

    Query the database for a user matching the provided ID.
    Returns the user object if found, otherwise None.

    parameters
    ----------
        session : Session
            Active SQLModel session for database operations.
        id : int | None
            The ID to search for.
    """
    get_user_by_id_statement = select(Users).where(
        Users.id == id
    )
    user = session.exec(get_user_by_id_statement).first()
    return user


def get_user_by_email(*, session: Session, email: EmailStr) -> Users | None:
    """
    Retrieve a user by their email.

    Query the database for a user matching the provided email address.
    Returns the user object if found, otherwise None.

    parameters
    ----------
        session : Session
            Active SQLModel session for database operations.
        email : EmailStr
            The email address to search for.
    """
    get_user_by_email_statement = select(Users).where(
        Users.email == email
    )
    user = session.exec(get_user_by_email_statement).first()
    return user


def get_user_by_username(*, session: Session, username: str) -> Users | None:
    """
    Retrieve a user by their username.

    Query the database for a user matching the provided username.
    Returns the user object if found, otherwise None.

    parameters
    ----------
        session : Session
            Active SQLModel session for database operations.
        username : str
            The username to search for.
    """
    get_user_by_username_statement = select(Users).where(
        Users.username == username
    )
    user = session.exec(get_user_by_username_statement).first()
    return user


def get_user_by_email_or_username(*, session: Session, identifire: EmailStr | str) -> Users | None:
    """
    Retrieve a user by their email or username.

    Query the database for a user matching the provided email address
    or username. Returns the user object if found, otherwise None.

    parameters
    ----------
        session : Session
            Active SQLModel session for database operations.
        identifire : EmailStr | str
            The email address or username to search for.
    """
    get_user_by_email_or_username_statement = select(Users).where(
        (Users.email == identifire) | (Users.username == identifire)
    )
    user = session.exec(get_user_by_email_or_username_statement).first()
    return user


def create_user(session: Session, validated_user: Users) -> Users:
    """
    Create the user in the database if the data is valid.

    Parameters
    ----------
    session : Session
        Active database session used to persist the user.
    validated_user : Users
        User instance containing data to be validated and saved.

    Returns
    -------
    Users
        The user instance after successful validation and user creation.
    """

    user_existing_with_email = get_user_by_email(session=session, email=validated_user.email)
    if user_existing_with_email:
        raise UserWithEmailAlreadyExistsException()

    user_existing_with_username = get_user_by_username(session=session, username=validated_user.username)
    if user_existing_with_username:
        raise UserWithUsernameAlreadyExistsException()

    if validated_user.password:
        validated_user.password = get_password_hash(validated_user.password)

    session.add(validated_user)
    session.commit()
    return validated_user


def update_user_data(*, session: Session, user_guid: str, profile_data: ProfileUpdate) -> Users:
    """
    Update the profile data for a user.

    Parameters
    ----------
    session : Session
        Active database session used to persist the updated user data.
    user_guid : str
        The GUID of the user whose profile is to be updated.
    profile_data : ProfileUpdate
        The new profile data to be applied to the user's profile.

    Returns
    -------
    Users
        The user instance after successful validation and user creation.
    """
    user = get_user_by_guid(session=session, guid=user_guid)

    if not user:
        raise UserNotFoundException()

    if profile_data.username != user.username:
        user_existing_with_username = get_user_by_username(session=session, username=profile_data.username)

        if user_existing_with_username and user_guid != user_existing_with_username.guid:
            raise UserWithUsernameAlreadyExistsException()

    # Update the user's profile data
    user.username = profile_data.username
    user.first_name = profile_data.first_name
    user.last_name = profile_data.last_name

    session.add(user)
    session.commit()
    session.refresh(user)

    return user

def update_user_password(*, session: Session, user_id: int | None, new_password: str) -> None:
    """
    Update the password for a user.

    Parameters
    ----------
    session : Session
        Active database session used to persist the updated user data.
    user_id : str
        The ID of the user whose password is to be updated.
    new_password : str
        The new plain text password to be set for the user.

    Returns
    -------
    None
    """
    user = get_user_by_id(session=session, id=user_id)

    if not user:
        raise UserNotFoundException()

    user.password = get_password_hash(new_password)

    session.add(user)
    session.commit()
