import logging
from typing import Any

from booking.core.config import settings
from booking.messaging.general import get_mq_client

log = logging.getLogger(__name__)


def user_created_exception_handler(
    *,
    original_queue: str,
    dead_letter_queue: str,
    data: dict[str, Any],
    exc: Exception,
) -> None:
    """
    Requeue or dead-letter a failed UserCreated event.
    """
    payload: dict[str, Any] = dict(data)
    retry_count = int(payload.get("retry_count") or 0)
    max_retry_count = settings.USER_CREATED_RETRY_COUNT

    mq_client = get_mq_client()

    if retry_count < max_retry_count:
        payload["retry_count"] = retry_count + 1
        mq_client.publish(original_queue, payload)
        log.warning(
            "Requeued user created event (retry_count=%s/%s): %s",
            payload["retry_count"],
            max_retry_count,
            exc,
        )
    else:
        mq_client.publish(dead_letter_queue, payload)
        log.error(
            "Moved user created event to dead letter queue (retry_count=%s): %s",
            retry_count,
            exc,
        )
