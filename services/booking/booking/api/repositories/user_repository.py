
from sqlmodel import Session, select

from booking.database.models.users import UsersReplica
from booking.schemas.mq_schemas import MqUserCreatedPayload


def upsert_user_replica(*, session: Session, payload: MqUserCreatedPayload) -> UsersReplica:
    """Insert or update a local user replica using stable user identifiers.

    Parameters
    ----------
    session : Session
        Active database session used to query and persist the replica.
    payload : MqUserCreatedPayload
        User-created message payload containing the replica data.

    Returns
    -------
    UsersReplica
        Newly inserted or updated, committed, and refreshed user replica.

    Raises
    ------
    SQLAlchemyError
        If the replica cannot be queried, committed, or refreshed.
    """
    replica = session.exec(
        select(UsersReplica).where(UsersReplica.email == payload.email)
    ).first()

    if replica is None:
        replica = session.exec(
            select(UsersReplica).where(UsersReplica.guid == payload.guid)
        ).first()

    if replica is None:
        replica = session.exec(
            select(UsersReplica).where(UsersReplica.username == payload.username)
        ).first()

    if replica is None:
        replica = UsersReplica(
            user_id=payload.id,
            guid=payload.guid,
            email=payload.email,
            username=payload.username,
            first_name=payload.first_name,
            last_name=payload.last_name,
            role=payload.role,
        )
    else:
        replica.user_id = payload.id
        replica.guid = payload.guid
        replica.email = payload.email
        replica.username = payload.username
        replica.first_name = payload.first_name
        replica.last_name = payload.last_name
        replica.role = payload.role

    session.add(replica)
    session.commit()
    session.refresh(replica)
    return replica


def get_user_replica_by_guid(*, session: Session, guid: str) -> UsersReplica | None:
    """Resolve a user's replica row by its public GUID.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    guid : str
        Public GUID of the user replica.

    Returns
    -------
    UsersReplica | None
        Matching user replica, or ``None`` if it does not exist.

    Raises
    ------
    SQLAlchemyError
        If the database query cannot be executed.
    """
    return session.exec(
        select(UsersReplica).where(UsersReplica.guid == guid)
    ).first()


def get_user_replica_by_id(*, session: Session, user_id: int | None) -> UsersReplica | None:
    """Resolve a user's replica row by its internal database ID.

    Parameters
    ----------
    session : Session
        Active database session used to retrieve the replica.
    user_id : int | None
        Internal user replica ID, or ``None`` when no lookup is required.

    Returns
    -------
    UsersReplica | None
        Matching user replica, or ``None`` for a missing ID or row.

    Raises
    ------
    SQLAlchemyError
        If the database lookup cannot be executed.
    """
    if user_id is None:
        return None
    return session.get(UsersReplica, user_id)
