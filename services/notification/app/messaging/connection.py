import time
import pika
from app.config import settings


def create_connection(retries: int = 10, delay: int = 3) -> pika.BlockingConnection:
    """
    Create RabbitMQ connection with retry & backoff.
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
