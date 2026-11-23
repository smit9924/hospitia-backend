from booking.core.config import settings
from booking.messaging.base import MQClient
from booking.messaging.rabbitmq.client import RabbitMQClient

_mq_client: MQClient | None = None


def get_mq_client() -> MQClient:
    """
    Gets the singleton message queue client instance.

    Creates the configured message queue client on first access and returns the
    same instance for subsequent calls.

    Returns:
        The configured message queue client instance.

    Raises:
        ValueError: If the configured message queue client type is not supported.
    """

    global _mq_client

    if _mq_client is None:
        _mq_client = create_mq_client()
    return _mq_client


def create_mq_client() -> MQClient:
    """
    Creates a new message queue client of the configured type.

    Each client owns its own broker connection; use `get_mq_client` for the
    shared one, and a separate client only for a component that publishes
    from its own thread (connections are not thread-safe).

    Returns:
        A new, not yet connected, message queue client.

    Raises:
        ValueError: If the configured message queue client type is not supported.
    """

    mq_client_type = settings.MQ_CLIENT_TYPE

    if mq_client_type is None or mq_client_type == 'rabbitmq':
        return RabbitMQClient()

    raise ValueError(f'Unsupported message queue client type: {mq_client_type}')
