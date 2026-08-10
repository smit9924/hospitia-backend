from notification.core.config import settings
from notification.messaging.base import MQConsumer
from notification.messaging.rabbitmq.consumer import RabbitMQConsumer

_mq_consumer: MQConsumer | None = None


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
