from typing import Any

from sqlmodel import Session

from dashboard.api.services.user_replica_service import upsert_replicated_user
from dashboard.database.db import engine
from dashboard.schemas.mq_schemas import MqDomainEvent, MqUserCreatedPayload


def user_created_handler(event: dict[str, Any]) -> None:
    """
    Consume a UserCreated domain event and upsert the local user replica.
    """
    envelope = MqDomainEvent.model_validate(event)
    payload = MqUserCreatedPayload.model_validate(envelope.payload)

    with Session(engine) as session:
        upsert_replicated_user(session=session, payload=payload)
