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
    def publish(
        self,
        destination: str,
        message: BaseSchema,
        routing_key: str | None = None,
    ) -> None:
        """
        Publishes a message to the given destination.

        @param destination Broker destination name. For RabbitMQ, this can be a queue or an exchange.
        @param message Message payload to publish.
        @param routing_key Optional routing key or topic key. Required when destination is an exchange.
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """
        Closes broker resources and connection.
        """
        raise NotImplementedError


class MQConsumer(ABC):
    """
    Base contract for message queue consumers.

    Concrete implementations are responsible for managing broker-specific
    connections, subscriptions, retries, acknowledgements, and message
    processing lifecycles.
    """

    @abstractmethod
    def connect(self) -> None:
        """
        Establishes connectivity with the messaging broker and validates that
        required resources exist.
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
    def start_consuming(self) -> None:
        """
        Starts consuming messages from all registered destinations.
        """
        raise NotImplementedError

    @abstractmethod
    def stop_consuming(self) -> None:
        """
        Gracefully stops all active consumers and prevents new messages from
        being processed.
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """
        Releases all broker resources and shuts down the consumer.
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
    dead_letter_queue: str | None

    @abstractmethod
    def declare(cls, channel: Any) -> None:
        """
        Declares the queue and any required broker-specific bindings.
        """
        raise NotImplementedError
