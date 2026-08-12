import logging
from typing import Any

from notification.core.config import settings
from notification.messaging.mq_client_general import get_mq_client

log = logging.getLogger(__name__)


def forgot_password_email_notification_exception_handler(
    *,
    original_queue: str,
    dead_letter_queue: str,
    data: dict[str, Any],
    exc: Exception,
) -> None:
    """
    Requeue or dead-letter a failed forgot-password email notification.

    Injects ``retry_count`` into the payload on first failure and publishes
    back to the original queue while under the configured limit; otherwise
    publishes to the dead-letter queue.
    """
    payload: dict[str, Any] = dict(data)
    retry_count = int(payload.get("retry_count") or 0)
    max_retry_count = settings.FORGOT_PASSWORD_EMAIL_RETRY_COUNT

    mq_client = get_mq_client()

    if retry_count < max_retry_count:
        payload["retry_count"] = retry_count + 1
        mq_client.publish(original_queue, payload)
        log.warning(
            "Requeued forgot password email notification "
            "(retry_count=%s/%s): %s",
            payload["retry_count"],
            max_retry_count,
            exc,
        )
    else:
        mq_client.publish(dead_letter_queue, payload)
        log.error(
            "Moved forgot password email notification to dead letter queue "
            "(retry_count=%s): %s",
            retry_count,
            exc,
        )


def verify_email_otp_email_notification_exception_handler(
    *,
    original_queue: str,
    dead_letter_queue: str,
    data: dict[str, Any],
    exc: Exception,
) -> None:
    """
    Requeue or dead-letter a failed verify-email OTP email notification.

    Injects ``retry_count`` into the payload on first failure and publishes
    back to the original queue while under the configured limit; otherwise
    publishes to the dead-letter queue.
    """
    payload: dict[str, Any] = dict(data)
    retry_count = int(payload.get("retry_count") or 0)
    max_retry_count = settings.VERIFY_EMAIL_OTP_EMAIL_RETRY_COUNT

    mq_client = get_mq_client()

    if retry_count < max_retry_count:
        payload["retry_count"] = retry_count + 1
        mq_client.publish(original_queue, payload)
        log.warning(
            "Requeued verify email OTP email notification "
            "(retry_count=%s/%s): %s",
            payload["retry_count"],
            max_retry_count,
            exc,
        )
    else:
        mq_client.publish(dead_letter_queue, payload)
        log.error(
            "Moved verify email OTP email notification to dead letter queue "
            "(retry_count=%s): %s",
            retry_count,
            exc,
        )
