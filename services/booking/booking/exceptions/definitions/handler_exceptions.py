from booking.exceptions.definitions.base import BaseException
from booking.types.error_codes import ErrorCodes


class HandlerNotFoundError(BaseException):
    """
    Raised when no handler is registered for a consumed queue.
    """

    def __init__(self, queue_name: str) -> None:
        self.queue_name = queue_name
        super().__init__(
            ErrorCodes.HANDLER_NOT_FOUND,
            f"No handler registered for queue '{queue_name}'.",
        )
