from contextlib import asynccontextmanager

from fastapi import FastAPI

from notification.core.config import settings
from notification.logging import configure_logging
from notification.messaging.mq_client_general import get_mq_client
from notification.messaging.mq_consumer_general import get_mq_consumer

configure_logging(settings.logging_settings())


def on_startup() -> None:
    """
    Contains operations to be performed when the application starts up.
    """
    mq_client = get_mq_client()
    mq_client.connect()

    mq_consumer = get_mq_consumer()
    mq_consumer.connect()
    mq_consumer.start_consuming()


def on_shutdown() -> None:
    """
    Contains operations to be performed when the application is shutting down.
    """
    mq_client = get_mq_client()
    mq_client.close()

    mq_consumer = get_mq_consumer()
    mq_consumer.stop_consuming()
    mq_consumer.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Lifespan function to handle startup and shutdown events.
    """
    on_startup()
    yield
    on_shutdown()


app = FastAPI(
    lifespan=lifespan
)
