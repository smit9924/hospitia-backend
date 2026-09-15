from sqlmodel import Session

from payment.api.repositories.user_repository import upsert_user_replica
from payment.database.models.users import UsersReplica
from payment.schemas.mq_schemas import MqUserCreatedPayload


def upsert_replicated_user(*, session: Session, payload: MqUserCreatedPayload) -> UsersReplica:
    """
    Apply a UserCreated event to the local UsersReplica table.
    """
    return upsert_user_replica(session=session, payload=payload)
