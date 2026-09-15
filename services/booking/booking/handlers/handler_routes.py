from collections.abc import Callable
from typing import Any

from booking.core.config import settings
from booking.exceptions.definitions.handler_exceptions import HandlerNotFoundError
from booking.handlers.user_handlers import user_created_handler

type MESSAGE_HANDLER = Callable[[dict[str, Any]], None]

MESSAGE_ROUTES: dict[str, MESSAGE_HANDLER] = {
    settings.USER_CREATED_QUEUE: user_created_handler,
}


def get_handler(queue_name: str) -> MESSAGE_HANDLER:
    """
    Retrieve the handler registered for the given queue.
    """
    try:
        return MESSAGE_ROUTES[queue_name]
    except Exception as ex:
        raise HandlerNotFoundError(queue_name) from ex
