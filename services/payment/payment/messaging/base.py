from abc import ABC, abstractmethod
from typing import Any

from payment.schemas.base_schemas import BaseSchema


class MQClient(ABC):
    """
    Base message queue client contract.

    Concrete MQ implementations should handle broker-specific connection,
    destination declaration, publishing, consuming, and shutdown behavior.
    """

    @abstractmethod
    def connect(self) -> None:
        """
        Establishes a connection to the message broker.
        """
        raise NotImplementedError

    @abstractmethod
    def declare_destinations(self) -> None:
        """
        Declares all required broker-specific messaging destinations.

        For RabbitMQ, this can include exchanges, queues, and bindings.
        For Kafka, this can include topics.
        """
        raise NotImplementedError

    @abstractmethod
    def publish(self, destination: str, message: BaseSchema) -> None:
        """
        Publishes a message to the given destination.

        @param destination Broker destination name. For RabbitMQ, this can be an exchange.
        @param message Message payload to publish.
        @param routing_key Optional routing key or topic key, depending on broker.
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """
        Closes broker resources and connection.
        """
        raise NotImplementedError


class MQExchangeBase(ABC):
    """
    Base contract for declaring message broker exchanges or equivalent routing resources.
    """

    name: str

    @abstractmethod
    def declare(cls, channel: Any) -> None:
        """
        Declares the exchange or equivalent broker resource.
        """
        raise NotImplementedError


class MQQueueBase(ABC):
    """
    Base contract for declaring message broker queues or equivalent destinations.
    """

    name: str

    @abstractmethod
    def declare(cls, channel: Any) -> None:
        """
        Declares the queue and any required broker-specific bindings.
        """
        raise NotImplementedError
