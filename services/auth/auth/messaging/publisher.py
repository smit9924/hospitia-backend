import json

import pika

from auth.core.config import settings
from auth.messaging.connection import RabbitMQClient


def publish_message(message: dict) -> None:
    channel = RabbitMQClient.get_channel()

    channel.basic_publish(
            exchange=settings.NOTIFICATION_EXCHANGE,
            routing_key=settings.EMAIL_ROUTING_KEY,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                priority=5,
                content_type="application/json",
            ),
        )
