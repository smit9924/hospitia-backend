import json
import pika
from auth.messaging.connection import create_connection
from auth.core.config import settings


def publish_message(message: dict) -> None:
    connection = create_connection()
    channel = connection.channel()

    try:
        channel.basic_publish(
            exchange=settings.NOTIFICATION_EXCHANGE,
            routing_key=settings.EMAIL_ROUTING_KEY,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                priority=5,
                content_type="application/json",
            ),
        )
    finally:
        connection.close()
