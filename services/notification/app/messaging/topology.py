from app.config import settings


def setup_topology(channel) -> None:
    """
    Declare exchange, queue and bindings.
    Safe to call multiple times.
    """

    # Exchange for notifications
    channel.exchange_declare(
        exchange=settings.notification_exchange,
        exchange_type=settings.notification_exchange_type,
        durable=True,
    )

    # Priority-enabled queue for email notifications
    channel.queue_declare(
        queue=settings.email_queue,
        durable=True,
        arguments={
            "x-max-priority": settings.max_priority,
        },
    )

    # Bind queue to exchange
    channel.queue_bind(
        exchange=settings.notification_exchange,
        queue=settings.email_queue,
        routing_key=settings.email_routing_key,
    )
