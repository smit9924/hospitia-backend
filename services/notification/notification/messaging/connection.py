import pika
from pika.adapters.blocking_connection import BlockingChannel

from notification.core.config import settings


class RabbitMQClient:
    """Singleton RabbitMQ client for managing connection and channel."""
    _connection = None
    _channel = None

    @classmethod
    def get_connection(cls) -> pika.BlockingConnection:
        """
        Get or create a RabbitMQ connection.

        Returns
        -------
            pika.BlockingConnection: Active RabbitMQ connection.
        """
        if cls._connection is None or cls._connection.is_closed:
            credentials = pika.PlainCredentials(
                settings.rabbitmq_username,
                settings.rabbitmq_password,
            )
            params = pika.ConnectionParameters(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                credentials=credentials,
            )
            cls._connection = pika.BlockingConnection(params)

        return cls._connection

    @classmethod
    def get_channel(cls) -> BlockingChannel:
        """
        Get or create a RabbitMQ channel.

        Returns
        -------
            BlockingChannel: Active RabbitMQ channel.
        """
        if cls._channel is None or cls._channel.is_closed:
            connection = cls.get_connection()
            cls._channel = connection.channel()
        return cls._channel

    @classmethod
    def stop_consumer(cls):
        """Gracefully stop the consumer by closing the RabbitMQ connection."""
        if cls._channel and cls._channel.is_open:
            cls._channel.stop_consuming()

    @classmethod
    def close_connection(cls):
        """Close the RabbitMQ connection and channel."""
        if cls._connection and cls._connection.is_open:
            cls._connection.close()
