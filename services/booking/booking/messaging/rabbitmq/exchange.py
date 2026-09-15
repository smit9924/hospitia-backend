from pika.adapters.blocking_connection import BlockingChannel
from pika.exchange_type import ExchangeType

from booking.messaging.base import MQExchangeBase


class RabbitMQExchange(MQExchangeBase):
    """
    Base RabbitMQ exchange declaration.
    """

    name: str
    exchange_type: ExchangeType
    durable: bool = True
    auto_delete: bool = False

    def __init__(self, name: str, exchange_type: ExchangeType, durable: bool = True, auto_delete: bool = False):
        self.name = name
        self.exchange_type = exchange_type
        self.durable = durable
        self.auto_delete = auto_delete

    def declare(self, channel: BlockingChannel) -> None:
        """
        Declares the RabbitMQ exchange.
        """

        channel.exchange_declare(
            exchange=self.name,
            exchange_type=self.exchange_type,
            durable=self.durable,
            auto_delete=self.auto_delete,
        )

