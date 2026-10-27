import logging
from typing import Any

from sqlmodel import Session

from booking.api.services.organization_user_mapping_service import (
    map_provisioned_manager,
)
from booking.api.services.user_replica_service import upsert_replicated_user
from booking.database.db import engine
from booking.schemas.mq_schemas import MqDomainEvent, MqUserCreatedPayload

log = logging.getLogger(__name__)


def user_created_handler(event: dict[str, Any]) -> None:
    """
    Consume a UserCreated domain event and upsert the local user replica.

    When the event carries an `organization_guid` (a provisioned MANAGER),
    the manager is then mapped to that organization; an invalid
    organization only skips the mapping, never the replica.
    """
    log.info("Started")
    envelope = MqDomainEvent.model_validate(event)
    payload = MqUserCreatedPayload.model_validate(envelope.payload)

    log.info(
        "Processing user created event event_id=%s guid=%s",
        envelope.event_id,
        payload.guid,
    )

    with Session(engine) as session:
        replica = upsert_replicated_user(session=session, payload=payload)
        log.info("User replica upserted guid=%s", payload.guid)

        if payload.organization_guid is not None:
            map_provisioned_manager(
                session=session,
                manager=replica,
                organization_guid=payload.organization_guid,
                created_by_guid=payload.created_by_guid,
            )
