from collections.abc import Callable

from booking.core.config import settings
from booking.exceptions.handlers.consumer_exception_handlers import (
    user_created_exception_handler,
)

type QUEUE_EXCEPTION_HANDLER = Callable[..., None]

EXCEPTION_ROUTES: dict[str, QUEUE_EXCEPTION_HANDLER] = {
    settings.USER_CREATED_QUEUE: user_created_exception_handler,
}


def get_exception_handler(queue_name: str) -> QUEUE_EXCEPTION_HANDLER | None:
    """
    Return the consumer exception handler registered for the given queue, if any.
    """
    return EXCEPTION_ROUTES.get(queue_name)
