import json
import logging

from app.messaging.connection import create_connection
from app.messaging.topology import setup_topology
from app.models.event import NotificationEvent
from app.models.enums import Channel
from app.config import settings

from app.channels.email.handler import handle as email_handler

log = logging.getLogger(__name__)


HANDLERS = {
    Channel.EMAIL: email_handler,
}


def run_consumer() -> None:
    """
    Start RabbitMQ consumer (blocking).
    This function owns the process lifecycle.
    """

    connection = create_connection()
    channel = connection.channel()

    setup_topology(channel)

    def on_message(ch, method, body: bytes):
        try:
            payload = json.loads(body)
            event = NotificationEvent(**payload)

            handler = HANDLERS.get(event.channel)
            if not handler:
                raise ValueError(f"No handler for channel {event.channel}")

            handler(event.payload)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as exc:
            log.exception("Failed to process message: %s", exc)

            # Do NOT requeue bad messages (future DLQ)
            ch.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False,
            )

    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=settings.email_queue,
        on_message_callback=on_message,
    )

    log.info("📨 Notification consumer started")
    channel.start_consuming()
