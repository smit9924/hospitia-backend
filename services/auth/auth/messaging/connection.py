import pika
from auth.core.config import settings


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
        settings.RABBITMQ_USERNAME,
        settings.RABBITMQ_PASSWORD,
    )

    params = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        credentials=credentials,
    )

    return pika.BlockingConnection(params)
