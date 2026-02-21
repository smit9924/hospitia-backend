from notification.core.config import settings


def setup_topology(channel) -> None:
    """
    Declare RabbitMQ messaging topology.

    Creates the required exchange, queue, and routing bindings
    used by the notification system.
    
    Parameters
    ----------
    
        channel : pika.channel.Channel
            Active RabbitMQ channel to declare topology on.
    """

    channel.exchange_declare(
        exchange=settings.notification_exchange,
        exchange_type=settings.notification_exchange_type,
        durable=True,
    )

    channel.queue_declare(
        queue=settings.email_queue,
        durable=True,
        arguments={
            "x-max-priority": settings.max_priority,
        },
    )

    channel.queue_bind(
        exchange=settings.notification_exchange,
        queue=settings.email_queue,
        routing_key=settings.email_routing_key,
    )
