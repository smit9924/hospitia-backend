from time import sleep

from pika import (
    BasicProperties,
    BlockingConnection,
    ConnectionParameters,
    PlainCredentials,
)
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import (
    AMQPChannelError,
    AMQPConnectionError,
    ChannelClosedByBroker,
    ConnectionClosed,
    StreamLostError,
)

from dashboard.core.config import settings
from dashboard.exceptions.definitions.messaging_queue_exceptions import (
    MQMessagePublishException,
    MQNotFoundException,
)
from dashboard.messaging.base import MQClient
from dashboard.schemas.base_schemas import BaseModel

from .exchange import RabbitMQExchange
from .queue import RabbitMQQueue


class RabbitMQClient(MQClient):
    """
    RabbitMQ client implementation using Pika.

    Handles connection setup, channel creation, destination declaration,
    message publishing, retry, recovery, and shutdown.
    """
    _connection: BlockingConnection | None = None
    _publish_channel: BlockingChannel | None = None

    def __init__(self) -> None:
        self._exchanges: dict[str, RabbitMQExchange] = {
            settings.EMAIL_NOTIFICATION_EXCHANGE: RabbitMQExchange(
                name=settings.EMAIL_NOTIFICATION_EXCHANGE,
                exchange_type=settings.EMAIL_NOTIFICATION_EXCHANGE_TYPE,
            ),
        }

        self._queues: dict[str, RabbitMQQueue] = {
            settings.FORGOT_PASSWORD_EMAIL_QUEUE: RabbitMQQueue(
                name=settings.FORGOT_PASSWORD_EMAIL_QUEUE,
                exchange_name=settings.EMAIL_NOTIFICATION_EXCHANGE,
                routing_key=settings.FORGOT_PASSWORD_EMAIL_QUEUE_ROUTING_KEY,
            ),
        }

    def connect(self) -> None:
        """
        Establishes the RabbitMQ connection and declares configured destinations.
        """

        self.__get_connection()
        self.declare_destinations()

    def declare_destinations(self) -> None:
        """
        Declares all configured RabbitMQ exchanges, queues, and bindings.
        """

        channel = self.__get_channel()

        try:
            for exchange in self._exchanges.values():
                exchange.declare(channel)

            for queue in self._queues.values():
                queue.declare(channel)
        finally:
            self.__close_channel(channel)

    def publish(self, destination: str, message: BaseModel) -> None:
        """
        Publishes a JSON message to the configured queue route.

        Args:
            destination: Registered queue name.
            message: Message payload to publish.

        Raises:
            MQNotFoundException: If the destination queue is not registered.
        """

        if destination not in self._queues:
            raise MQNotFoundException()

        queue = self._queues[destination]
        self.__publish_with_retry(queue, message)

    def close(self) -> None:
        """
        Closes the RabbitMQ connection when it is open.
        """
        if self._publish_channel and self._publish_channel.is_open:
            self._publish_channel.close()

        if self._connection and self._connection.is_open:
            self._connection.close()

    def __publish_with_retry(self, queue: RabbitMQQueue, message: BaseModel) -> None:
        """
        Publishes a message with retry for recoverable RabbitMQ failures.

        Args:
            queue: Registered RabbitMQ queue route.
            message: Message payload to publish.
        """

        last_error: Exception | None = None

        for attempt in range(1, settings.RABBITMQ_PUBLISH_RETRY_ATTEMPTS + 1):
            try:
                self.__publish_once(queue, message)
                return
            except (
                AMQPConnectionError,
                AMQPChannelError,
                ChannelClosedByBroker,
                ConnectionClosed,
                StreamLostError,
            ) as error:
                last_error = error
                self.__reset_connection()

                if attempt < settings.RABBITMQ_PUBLISH_RETRY_ATTEMPTS:
                    sleep(settings.RABBITMQ_PUBLISH_RETRY_DELAY)

        if last_error is not None:
            raise MQMessagePublishException() from last_error

    def __publish_once(self, queue: RabbitMQQueue, message: BaseModel) -> None:
        """
        Publishes a message once using a fresh RabbitMQ channel.

        Args:
            queue: Registered RabbitMQ queue route.
            message: Message payload to publish.
        """
        # Establish connection if lost with any reason
        self.__get_connection()

        if self._publish_channel is None or self._publish_channel.is_closed:
            self._publish_channel = self.__get_channel()
            self._publish_channel.confirm_delivery()


        self._publish_channel.basic_publish(
            exchange=queue.exchange_name,
            routing_key=queue.routing_key,
            body=message.model_dump_json().encode('utf-8'),
            properties=BasicProperties(
                content_type='application/json',
                delivery_mode=2,
            ),
            mandatory=True,
        )

    def __get_connection(self) -> None:
        """
        Creates a RabbitMQ connection when no active connection exists.
        """

        if self._connection is not None and self._connection.is_open:
            return

        credentials = PlainCredentials(
            settings.RABBITMQ_USERNAME,
            settings.RABBITMQ_PASSWORD,
        )

        params = ConnectionParameters(
            host=settings.RABBITMQ_HOST,  # type: ignore[arg-type]
            port=settings.RABBITMQ_PORT,  # type: ignore[arg-type]
            credentials=credentials,  # type: ignore[arg-type]
            heartbeat=settings.RABBITMQ_HEART_BEAT,  # type: ignore[arg-type]
            blocked_connection_timeout=settings.RABBITMQ_CONNECTION_TIMEOUT,  # type: ignore[arg-type]
            connection_attempts=settings.RABBITMQ_RETRY_ATTEMPTS,  # type: ignore[arg-type]
            retry_delay=settings.RABBITMQ_RETRY_DELAY,  # type: ignore[arg-type]
        )

        self._connection = BlockingConnection(params)

    def __get_channel(self) -> BlockingChannel:
        """
        Creates a fresh RabbitMQ channel from the active connection.

        Returns:
            Active RabbitMQ channel.
        """

        self.__get_connection()

        if self._connection is None or self._connection.is_closed:
            raise AMQPConnectionError('RabbitMQ connection is not established.')

        return self._connection.channel()

    def __reset_connection(self) -> None:
        """
        Resets the RabbitMQ connection after a recoverable broker failure.
        """

        try:
            self.close()
        finally:
            self._connection = None

    def __close_channel(self, channel: BlockingChannel) -> None:
        """
        Closes a RabbitMQ channel when it is open.

        Args:
            channel: RabbitMQ channel to close.
        """

        if channel.is_open:
            channel.close()
