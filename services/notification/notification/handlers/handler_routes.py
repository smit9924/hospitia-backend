from collections.abc import Callable
from typing import Any

from notification.core.config import settings
from notification.exceptions.definitions.messaging_queue_exceptions import (
    HandlerNotFoundError,
)
from notification.handlers.email_handlers import (
    forgot_password_email_handler,
    verify_email_otp_email_handler,
)

type MESSAGE_HANDLER = Callable[[dict[str, Any]], None]

MESSAGE_ROUTES: dict[str, MESSAGE_HANDLER] = {
    settings.FORGOT_PASSWORD_EMAIL_QUEUE: forgot_password_email_handler,
    settings.VERIFY_EMAIL_OTP_EMAIL_QUEUE: verify_email_otp_email_handler,
}


def get_handler(routing_key: str) -> MESSAGE_HANDLER:
    """
    Retrieve the appropriate handler function based on the provided routing key.

    Parameters
    ----------
    routing_key : str
        The routing key associated with the message queue to be processed.
    """

    try:
        return MESSAGE_ROUTES[routing_key]
    except Exception as ex:
        raise HandlerNotFoundError(routing_key) from ex
