from sqlmodel import Session, select

from auth.database.models.users import Users


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
