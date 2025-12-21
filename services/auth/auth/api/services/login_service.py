from sqlmodel import Session, select

from auth.core.security import verify_password
from auth.database.models.users import Users
from auth.types.enums import AuthType


def get_user_by_email_or_username(*, session: Session, email_or_username: str) -> Users | None:
    """
    Retrieve a user by their email or username.

    Query the database for a user matching the provided email address
    or username. Returns the user object if found, otherwise None.

    parameters
    ----------
        session : Session
            Active SQLModel session for database operations.
        email_or_username : str
            The email address or username to search for.
    """
    get_user_by_email_or_username_statement = select(Users).where(
        (Users.email == email_or_username) | (Users.username == email_or_username)
    )
    user = session.exec(get_user_by_email_or_username_statement).first()
    return user


def authenticate_manual_user(*, session: Session, email_or_username: str, password: str) -> Users | None:
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
    user = get_user_by_email_or_username(session=session, email_or_username=email_or_username)
    if not user:
        return None
    if not user.auth_type == AuthType.MANUAL:
        return None
    if (not user.password) or (not verify_password(plain_password=password, hashed_password=user.password)):
        return None

    return user
