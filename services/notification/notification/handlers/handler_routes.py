from collections.abc import Callable
from typing import Any

from notification.core.config import settings
from notification.handlers.email_handlers import (
    forgot_password_email_handler,
)

type EMAIL_MESSAGE_HANDLER = Callable[[dict[str, Any]], None]

MESSAGE_ROUTES: dict[str, EMAIL_MESSAGE_HANDLER] = {
    settings.FORGOT_PASSWORD_EMAIL_QUEUE: forgot_password_email_handler,
}


def get_handler(routing_key: str) -> EMAIL_MESSAGE_HANDLER:
    """
    Retrieve the appropriate handler function based on the provided routing key.

    Parameters
    ----------
    routing_key : str
        The routing key associated with the message queue to be processed.
    """

    try:
        return MESSAGE_ROUTES[routing_key]
    except KeyError:
        raise ValueError(f"No handler registered for '{routing_key}'")
