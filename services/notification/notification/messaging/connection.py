import pika
from backend.services.notification.notification.core.config import settings


def create_connection() -> pika.BlockingConnection:
    """
    Create a blocking RabbitMQ connection.

    Configures authentication and connection parameters
    using application settings.

    Returns
    -------
    pika.BlockingConnection
        Active RabbitMQ connection instance.
    """

    credentials = pika.PlainCredentials(
        settings.rabbitmq_username,
        settings.rabbitmq_password,
    )

    params = pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        credentials=credentials,
        heartbeat=60,
    )

    return pika.BlockingConnection(params)
