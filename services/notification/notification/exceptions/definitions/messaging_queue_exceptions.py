from notification.exceptions.definitions.base import BaseException


class MQNotFoundException(BaseException):
    """
    Raised when a requested messaging queue cannot be found.
    """

    def __init__(
        self,
        message: str = "The requested messaging queue was not found."
    ) -> None:
        super().__init__(message)


class MQMessagePublishException(BaseException):
    """
    Raised when a message cannot be published to the messaging queue.
    """

    def __init__(
        self,
        message: str = "Failed to publish the message to the messaging queue."
    ) -> None:
        super().__init__(message)


class HandlerNotFoundError(BaseException):
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
