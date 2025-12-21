from sqlmodel import Session

from auth.core.security import get_password_hash
from auth.database.models.users import Users


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

    if user_validated.password:
        user_validated.password = get_password_hash(user_validated.password)

    session.add(user_validated)
    session.commit()
    return user
