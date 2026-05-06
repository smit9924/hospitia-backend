import json
import logging
from typing import cast

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from notification.channels.email.handler import handle as email_handler
from notification.core.config import settings
from notification.messaging.connection import RabbitMQClient
from notification.messaging.topology import setup_topology
from notification.schemas.event import NotificationEvent
from notification.types.enums import Channel

log = logging.getLogger(__name__)


HANDLERS = {
    Channel.EMAIL: email_handler,
}


def run_consumer() -> None:
    """
    Start the RabbitMQ notification consumer (blocking).
    - Establish RabbitMQ connection.
    - Declare messaging topology (exchange, queues, bindings).
    - Consume notification events from the configured queue.
    - Route events to the appropriate channel handler.
    - Acknowledge successfully processed messages.
    - Reject invalid or failed messages without requeueing.
    """
    log.info("Connecting to RabbitMQ...")

    channel = RabbitMQClient.get_channel()

    setup_topology(channel)

    def on_message(ch:BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes):
        """
        RabbitMQ message callback.

        Workflow
        --------
        - Deserialize incoming JSON message.
        - Validate payload using NotificationEvent schema.
        - Resolve handler based on notification channel.
        - Execute handler with event payload.
        - Acknowledge message on success.

        Error Handling
        --------------
        - Any exception results in message rejection.
        - Messages are NOT requeued to prevent infinite retries.
        """

        try:
            payload = json.loads(body)
            event = NotificationEvent(**payload)

            handler = HANDLERS.get(event.channel)
            if not handler:
                raise ValueError(f"No handler for channel {event.channel}")

            handler(event)

            ch.basic_ack(delivery_tag=cast(int,method.delivery_tag))

        except Exception as exc:
            log.exception("Failed to process message: %s", exc)

            # Do NOT requeue bad messages (future DLQ)
            ch.basic_nack(
                delivery_tag=cast(int,method.delivery_tag),
                requeue=False,
            )

    channel.basic_consume(
        queue=settings.email_queue,
        on_message_callback=on_message,
    )

    log.info("Notification consumer started")
    channel.start_consuming()
