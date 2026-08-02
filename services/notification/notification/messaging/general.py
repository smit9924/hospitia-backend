from notification.core.config import settings
from notification.messaging.base import MQClient, MQConsumer
from notification.messaging.rabbitmq.client import RabbitMQClient
from notification.messaging.rabbitmq.consumer import RabbitMQConsumer

_mq_client: MQClient | None = None
_mq_consumer: MQConsumer | None = None


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

    if _mq_client is not None:
        return _mq_client

    mq_client_type = settings.MQ_CLIENT_TYPE

    if mq_client_type is None or mq_client_type == 'rabbitmq':
        _mq_client = RabbitMQClient()
        return _mq_client

    raise ValueError(f'Unsupported message queue client type: {mq_client_type}')


def get_mq_consumer() -> MQConsumer:
    """
    Gets the singleton message queue consumer instance.

    Creates the configured message queue consumer on first access and returns the
    same instance for subsequent calls.

    Returns:
        The configured message queue consumer instance.
    """
    global _mq_consumer

    if _mq_consumer is not None:
        return _mq_consumer

    mq_type = settings.MQ_CLIENT_TYPE

    if mq_type is None or mq_type == 'rabbitmq':
        _mq_consumer = RabbitMQConsumer()
        return _mq_consumer

    raise ValueError(f'Unsupported message queue client type: {mq_type}')
