
from payment.exceptions.definitions.base import BaseException
from payment.types.error_codes import ErrorCodes


class MQNotFoundException(BaseException):
    """
    Raised when a requested messaging queue cannot be found.
    """

    def __init__(
        self,
        message: str = "The requested messaging queue was not found."
    ) -> None:
        super().__init__(ErrorCodes.MQ_NOT_FOUND, message)


class MQMessagePublishException(BaseException):
    """
    Raised when a message cannot be published to the messaging queue.
    """

    def __init__(
        self,
        message: str = "Failed to publish the message to the messaging queue."
    ) -> None:
        super().__init__(ErrorCodes.MQ_MESSAGE_PUBLISH_FAILED, message)
