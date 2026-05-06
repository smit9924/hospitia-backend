import pika
from pika.adapters.blocking_connection import BlockingChannel

from auth.core.config import settings


class RabbitMQClient:
    _connection = None

    @classmethod
    def get_connection(cls) -> pika.BlockingConnection:
        # Check if connection exists and is open
        if cls._connection is None or cls._connection.is_closed:
            credentials = pika.PlainCredentials(
                settings.RABBITMQ_USERNAME,
                settings.RABBITMQ_PASSWORD,
            )

            # Pika internally expects arguments typed as type[_DEFAULT], which causes
            # type-checking conflicts with the provided settings values. Therefore,
            # type checking is ignored for these parameters.
            params = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST, #type: ignore[arg-type]
                port=settings.RABBITMQ_PORT, #type: ignore[arg-type]
                credentials=credentials, #type: ignore[arg-type]
            )
            cls._connection = pika.BlockingConnection(params)

        return cls._connection

    @classmethod
    def get_channel(cls) -> BlockingChannel:
        """Channels are lightweight; you can create them as needed
        from the singleton connection."""
        connection = cls.get_connection()
        return connection.channel()

    @classmethod
    def close_connection(cls):
        "Call this when the application is shutting down to cleanly close the RabbitMQ connection."
        if cls._connection and cls._connection.is_open:
            cls._connection.close()
