from sqlmodel import Session

from dashboard.api.repositories.user_repository import upsert_user_replica
from dashboard.database.models.users import UsersReplica
from dashboard.schemas.mq_schemas import MqUserCreatedPayload


def upsert_replicated_user(*, session: Session, payload: MqUserCreatedPayload) -> UsersReplica:
    """
    Apply a UserCreated event to the local UsersReplica table.
    """
    return upsert_user_replica(session=session, payload=payload)
