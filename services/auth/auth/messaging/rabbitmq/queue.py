from typing import Any

from pika.adapters.blocking_connection import BlockingChannel

from auth.messaging.base import MQQueueBase


class RabbitMQQueue(MQQueueBase):
    """
    RabbitMQ queue declaration with exchange binding support.
    """

    name: str
    exchange_name: str
    routing_key: str
    durable: bool
    auto_delete: bool
    arguments: dict[str, Any] | None

    def __init__(
        self,
        name: str,
        exchange_name: str,
        routing_key: str,
        durable: bool = True,
        auto_delete: bool = False,
        arguments: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self.durable = durable
        self.auto_delete = auto_delete
        self.arguments = arguments

    def declare(self, channel: BlockingChannel) -> None:
        """
        Declares the RabbitMQ queue and binds it to the configured exchange.

        Args:
            channel: Active RabbitMQ channel.
        """

        channel.queue_declare(
            queue=self.name,
            durable=self.durable,
            auto_delete=self.auto_delete,
            arguments=self.arguments,
        )

        channel.queue_bind(
            exchange=self.exchange_name,
            queue=self.name,
            routing_key=self.routing_key,
        )
