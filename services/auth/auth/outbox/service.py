import logging
import uuid
from datetime import UTC, datetime

from sqlmodel import Session

from auth.api.repositories.outbox_repository import (
    claim_unprocessed_user_outbox,
    mark_user_outbox_processed,
)
from auth.core.config import settings
from auth.database.db import engine
from auth.database.models.users_outbox import UsersOutbox
from auth.messaging.general import get_mq_client
from auth.schemas.mq_schemas import MqDomainEvent, MqUserCreatedPayload

log = logging.getLogger(__name__)


def process_pending_user_outbox() -> None:
    """
    Publish unprocessed user-created outbox rows and mark them processed.

    Broker topology comes from application settings, not from the outbox table.
    Failed publishes leave the row unprocessed so the next poll retries.
    """
    with Session(engine) as session:
        outbox_entries = claim_unprocessed_user_outbox(
            session=session,
            batch_size=settings.OUTBOX_BATCH_SIZE,
        )
        if not outbox_entries:
            return

        for outbox_entry in outbox_entries:
            _publish_user_created_event(outbox_entry)
            mark_user_outbox_processed(session=session, outbox_entry=outbox_entry)

        session.commit()
        log.info("Processed %s user-created outbox row(s)", len(outbox_entries))


def _publish_user_created_event(outbox_entry: UsersOutbox) -> None:
    """
    Publish a user-created domain event for a single outbox snapshot.
    """
    event = MqDomainEvent(
        event_id=uuid.uuid4(),
        event_type=settings.USER_CREATED_EVENT_TYPE,
        occurred_at=datetime.now(UTC),
        payload=MqUserCreatedPayload(
            id=outbox_entry.user_id,
            guid=outbox_entry.guid,
            email=outbox_entry.email,
            username=outbox_entry.username,
            first_name=outbox_entry.first_name,
            last_name=outbox_entry.last_name,
            role=outbox_entry.role,
        ).model_dump(mode="json"),
    )
    get_mq_client().publish(
        settings.USER_EVENTS_EXCHANGE,
        event,
        settings.USER_CREATED_ROUTING_KEY,
    )
    log.info(
        "User created event published event_id=%s guid=%s outbox_id=%s",
        event.event_id,
        outbox_entry.guid,
        outbox_entry.id,
    )
