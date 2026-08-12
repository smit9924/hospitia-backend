from collections.abc import Callable

from notification.core.config import settings
from notification.exceptions.handlers.handler_exceptions_handlers import (
    forgot_password_email_notification_exception_handler,
    verify_email_otp_email_notification_exception_handler,
)

type QUEUE_EXCEPTION_HANDLER = Callable[..., None]

# Maps each consumed queue to its failure handler (retry / DLQ).
EXCEPTION_ROUTES: dict[str, QUEUE_EXCEPTION_HANDLER] = {
    settings.FORGOT_PASSWORD_EMAIL_QUEUE: forgot_password_email_notification_exception_handler,
    settings.VERIFY_EMAIL_OTP_EMAIL_QUEUE: verify_email_otp_email_notification_exception_handler,
}


def get_exception_handler(queue_name: str) -> QUEUE_EXCEPTION_HANDLER | None:
    """
    Return the exception handler registered for the given queue, if any.
    """
    return EXCEPTION_ROUTES.get(queue_name)
