from uuid import UUID

from pydantic import EmailStr
from sqlmodel import Session, select

from booking.database.models.users import UsersReplica
from booking.schemas.mq_schemas import MqUserCreatedPayload


def upsert_user_replica(*, session: Session, payload: MqUserCreatedPayload) -> UsersReplica:
    """
    Insert or update a local user replica using email as the stable identity.
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
        )
    else:
        replica.user_id = payload.id
        replica.guid = payload.guid
        replica.email = payload.email
        replica.username = payload.username
        replica.first_name = payload.first_name
        replica.last_name = payload.last_name

    session.add(replica)
    session.commit()
    session.refresh(replica)
    return replica
