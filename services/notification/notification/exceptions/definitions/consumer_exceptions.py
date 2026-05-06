from notification.exceptions.definitions.base import NotificationBaseException


class HandlerNotFoundError(NotificationBaseException):
    """
    Raised when no handler is registered for the incoming
    notification channel.

    Parameters
    ----------
    channel : str
        The channel value extracted from the event envelope.
    """

    def __init__(self, channel: str) -> None:
        self.channel = channel
        super().__init__(
            message=f"No handler registered for channel '{channel}'.",
        )

class MessageDeserializationError(NotificationBaseException):
    """
    Raised when the raw RabbitMQ message body cannot be
    deserialized (e.g. malformed JSON).

    Parameters
    ----------
    original : Exception
        The underlying json.JSONDecodeError.
    """

    def __init__(self, original: Exception) -> None:
        self.original = original
        super().__init__(
            message=f"Failed to deserialize message body: {original}",
        )
