from notification.exceptions.definitions.base import NotificationBaseException
from notification.types.enums import Channel


class DeliveryError(NotificationBaseException):
    """
    Raised when a notification channel fails to deliver a message.

    The `retryable` flag controls consumer behavior:
    - True  → transient failure (e.g. SMTP timeout) → nack + requeue
    - False → permanent failure (e.g. auth error)   → nack + discard

    Parameters
    ----------
    channel : Channel
        The delivery channel that failed.
    original : Exception
        The underlying exception from the transport layer.

    """

    def __init__(
        self,
        channel: Channel,
        original: Exception,
        retryable: bool = False,
    ) -> None:
        self.channel = channel
        self.original = original
        super().__init__(
            message=f"Delivery failed on channel '{channel}': {original}",
        )


class SmtpAuthenticationError(DeliveryError):
    """
    Raised when SMTP login fails due to invalid credentials.
    """

    def __init__(self, original: Exception) -> None:
        super().__init__(
            channel=Channel.EMAIL,
            original=original,
        )


class SmtpConnectionError(DeliveryError):
    """
    Raised when the SMTP server is unreachable or the connection
    is refused.
    """

    def __init__(self, original: Exception) -> None:
        super().__init__(
            channel=Channel.EMAIL,
            original=original,
        )


class SmtpTransmissionError(DeliveryError):
    """
    Raised when the email is partially accepted or the DATA command
    fails mid-transmission. Treated as transient.
    """

    def __init__(self, original: Exception) -> None:
        super().__init__(
            channel=Channel.EMAIL,
            original=original,
        )
