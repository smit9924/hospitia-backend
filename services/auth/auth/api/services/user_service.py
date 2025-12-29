from pydantic import EmailStr
from sqlmodel import Session, select

from auth.core.security import get_password_hash
from auth.database.models.users import Users
from auth.exceptions.definitions.validation_exceptions import (
    UserWithEmailAlreadyExistsException,
)


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


def validate_and_create_user(session: Session, user: Users) -> Users:
    """
    Validate user data and create the user in the database if the data is valid.

    Parameters
    ----------
    session : Session
        Active database session used to persist the user.
    user : Users
        User instance containing data to be validated and saved.

    Returns
    -------
    Users
        The user instance after successful validation and user creation.
    """

    user_validated = Users.model_validate(user)

    user_existing_with_email = get_user_by_email(session=session, email=user.email)
    if user_existing_with_email:
        raise UserWithEmailAlreadyExistsException()

    user_existing_with_username = get_user_by_username(session=session, username=user.username)
    if user_existing_with_username:
        raise UserWithEmailAlreadyExistsException()

    if user_validated.password:
        user_validated.password = get_password_hash(user_validated.password)

    session.add(user_validated)
    session.commit()
    return user
