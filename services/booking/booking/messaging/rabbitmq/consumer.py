import json
from threading import Event, Thread
from time import sleep
from typing import Any

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
from pika.spec import Basic

from booking.core.config import settings
from booking.exceptions.consumer_registry import get_exception_handler
from booking.handlers.handler_routes import MESSAGE_HANDLER, get_handler
from booking.messaging.base import MQConsumer
from booking.messaging.general import get_mq_client

from .exchange import RabbitMQExchange
from .queue import RabbitMQQueue


class RabbitMQConsumer(MQConsumer):
    """
    RabbitMQ consumer implementation.

    Every registered queue gets its own thread, BlockingConnection,
    BlockingChannel, and retry loop.
    """

    def __init__(self) -> None:
        self._stop_event = Event()
        self._consumer_threads: dict[str, Thread] = {}
        self._consumer_connection_pool: dict[str, BlockingConnection] = {}
        self._consumer_channel_pool: dict[str, BlockingChannel] = {}

        self._consumer_handlers: dict[str, MESSAGE_HANDLER] = {
            settings.USER_CREATED_QUEUE: get_handler(settings.USER_CREATED_QUEUE),
        }

        self._exchanges: dict[str, RabbitMQExchange] = {
            settings.USER_EVENTS_EXCHANGE: RabbitMQExchange(
                name=settings.USER_EVENTS_EXCHANGE,
                exchange_type=settings.USER_EVENTS_EXCHANGE_TYPE,
            ),
        }

        self._queues: dict[str, RabbitMQQueue] = {
            settings.USER_CREATED_QUEUE: RabbitMQQueue(
                name=settings.USER_CREATED_QUEUE,
                exchange_name=settings.USER_EVENTS_EXCHANGE,
                routing_key=settings.USER_CREATED_QUEUE_ROUTING_KEY,
                dead_letter_queue=settings.USER_CREATED_DEAD_LETTER_QUEUE,
            ),
            settings.USER_CREATED_DEAD_LETTER_QUEUE: RabbitMQQueue(
                name=settings.USER_CREATED_DEAD_LETTER_QUEUE,
                exchange_name=settings.USER_EVENTS_EXCHANGE,
                routing_key=settings.USER_CREATED_DEAD_LETTER_QUEUE_ROUTING_KEY,
            ),
        }

    # ******************
    # Life cycle methods
    # ******************

    def connect(self) -> None:
        """
        Validate connectivity and declare exchanges/queues.

        Connections used for consuming are created lazily by each worker thread.
        """

        self.declare_destinations()

    def declare_destinations(self) -> None:
        connection = self.__create_connection()
        channel = connection.channel()

        try:
            for exchange in self._exchanges.values():
                exchange.declare(channel)

            for queue in self._queues.values():
                queue.declare(channel)

        finally:
            if channel.is_open:
                channel.close()

            if connection.is_open:
                connection.close()

    def start_consuming(self) -> None:
        """
        Start one consumer thread per queue.
        """

        self._stop_event.clear()

        for destination, handler in self._consumer_handlers.items():
            if destination in self._consumer_threads:
                continue

            thread = Thread(
                target=self.__consume_queue_with_retry,
                args=(destination, handler),
                daemon=True,
                name=f"rabbitmq-{destination}",
            )
            thread.start()
            self._consumer_threads[destination] = thread

    def stop_consuming(self) -> None:
        """
        Stop all consumer threads.
        """

        self._stop_event.set()

        # stop_consuming() unblocks start_consuming()
        for channel in self._consumer_channel_pool.values():
            try:
                if channel.is_open:
                    channel.stop_consuming()
            except Exception:
                pass

        for thread in self._consumer_threads.values():
            thread.join(timeout=5)

        self._consumer_threads.clear()

    def close(self) -> None:
        """
        Shutdown consumer completely.
        """

        self.stop_consuming()

        for channel in self._consumer_channel_pool.values():
            self.__close_channel(channel)

        self._consumer_channel_pool.clear()

        for connection in self._consumer_connection_pool.values():
            self.__close_connection(connection)

        self._consumer_connection_pool.clear()
    # end of life cycle methods

    # ***********************
    # Internal helper methods
    # ***********************

    def __consume_queue_with_retry(
        self,
        destination: str,
        handler: MESSAGE_HANDLER,
    ) -> None:
        """
        Independent retry loop for one queue.
        """

        while not self._stop_event.is_set():
            try:
                self.__consume_queue(destination, handler)
            except (
                AMQPConnectionError,
                AMQPChannelError,
                ChannelClosedByBroker,
                ConnectionClosed,
                StreamLostError,
            ):
                self.__cleanup_queue(destination)
                if self._stop_event.is_set():
                    break
                sleep(settings.RABBITMQ_CONSUMER_RETRY_DELAY)
            except Exception:
                self.__cleanup_queue(destination)
                if self._stop_event.is_set():
                    break
                sleep(settings.RABBITMQ_CONSUMER_RETRY_DELAY)

    def __consume_queue(
        self,
        destination: str,
        handler: MESSAGE_HANDLER,
    ) -> None:
        channel = self.__get_consumer_channel(destination)
        queue = self._queues[destination]
        queue.declare(channel)

        channel.basic_qos(
            prefetch_count=settings.RABBITMQ_CONSUMER_PREFETCH_COUNT,
        )

        channel.basic_consume(
            queue=queue.name,
            on_message_callback=self.__build_consumer_callback(destination, handler),
            auto_ack=False,
        )
        channel.start_consuming()

    # -------------------------------------------------------------------------
    # Callback
    # -------------------------------------------------------------------------

    def __build_consumer_callback(
        self,
        destination: str,
        handler: MESSAGE_HANDLER,
    ):
        def callback(
            channel: BlockingChannel,
            method: Basic.Deliver,
            _properties: BasicProperties,
            body: bytes,
        ) -> None:
            if method.delivery_tag is None:
                raise ValueError("Received message without a delivery tag.")

            message: dict[str, Any] | None = None

            try:
                message = json.loads(body.decode("utf-8"))
                handler(message)
                channel.basic_ack(delivery_tag=method.delivery_tag)
            except json.JSONDecodeError:
                self.__dead_letter_invalid_json(destination, body)
                channel.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as exc:
                exception_handler = get_exception_handler(destination)
                dead_letter_queue = self._queues[destination].dead_letter_queue

                if (
                    exception_handler is not None
                    and dead_letter_queue is not None
                    and message is not None
                ):
                    exception_handler(
                        original_queue=destination,
                        dead_letter_queue=dead_letter_queue,
                        data=message,
                        exc=exc,
                    )
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    channel.basic_nack(
                        delivery_tag=method.delivery_tag,
                        requeue=False,
                    )

        return callback

    def __dead_letter_invalid_json(self, destination: str, body: bytes) -> None:
        """
        Dead letter an invalid JSON message.
        """

        dead_letter_queue = self._queues[destination].dead_letter_queue
        if dead_letter_queue is None:
            return

        get_mq_client().publish(
            dead_letter_queue,
            {
                "raw_body": body.decode("utf-8", errors="replace"),
                "error": "json_decode",
            },
        )

    # -------------------------------------------------------------------------
    # Connection management
    # -------------------------------------------------------------------------
    def __get_consumer_channel(self, destination: str) -> BlockingChannel:
        """
        Returns the dedicated consumer channel for a queue.

        A new channel is created lazily if one does not already exist.
        """
        channel = self._consumer_channel_pool.get(destination)
        if channel is not None and channel.is_open:
            return channel

        connection = self.__get_consumer_connection(destination)
        channel = connection.channel()
        channel.basic_qos(prefetch_count=settings.RABBITMQ_CONSUMER_PREFETCH_COUNT)
        self._consumer_channel_pool[destination] = channel
        return channel

    def __get_consumer_connection(self, destination: str) -> BlockingConnection:
        """
        Returns the dedicated RabbitMQ connection for a queue.
        """
        connection = self._consumer_connection_pool.get(destination)
        if connection is not None and connection.is_open:
            return connection

        connection = self.__create_connection()
        self._consumer_connection_pool[destination] = connection
        return connection

    def __create_connection(self) -> BlockingConnection:
        """
        Creates a brand new BlockingConnection.
        """

        credentials = PlainCredentials(
            settings.RABBITMQ_USERNAME,
            settings.RABBITMQ_PASSWORD,
        )
        parameters = ConnectionParameters(
            host=settings.RABBITMQ_HOST,  # type: ignore
            port=settings.RABBITMQ_PORT,  # type: ignore
            credentials=credentials,  # type: ignore
            heartbeat=settings.RABBITMQ_HEART_BEAT,  # type: ignore
            blocked_connection_timeout=settings.RABBITMQ_CONNECTION_TIMEOUT,  # type: ignore
            connection_attempts=settings.RABBITMQ_RETRY_ATTEMPTS,  # type: ignore
            retry_delay=settings.RABBITMQ_RETRY_DELAY,  # type: ignore
        )
        return BlockingConnection(parameters)

    def __cleanup_queue(self, destination: str) -> None:
        channel = self._consumer_channel_pool.pop(destination, None)
        if channel is not None:
            self.__close_channel(channel)

        connection = self._consumer_connection_pool.pop(destination, None)
        if connection is not None:
            self.__close_connection(connection)

    def __close_channel(self, channel: BlockingChannel | None) -> None:
        if channel is None:
            return
        try:
            if channel.is_open:
                channel.close()
        except Exception:
            pass

    def __close_connection(self, connection: BlockingConnection | None) -> None:
        if connection is None:
            return
        try:
            if connection.is_open:
                connection.close()
        except Exception:
            pass
