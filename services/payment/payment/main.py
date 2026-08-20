from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from payment.api.routes.main import api_router
from payment.core.config import settings
from payment.exceptions.registry import get_exception_handlers
from payment.messaging.base import MQClient
from payment.messaging.general import get_mq_client
from payment.messaging.mq_consumer_general import get_mq_consumer
from payment.middleware import REQUEST_ID_HEADER, RequestIdMiddleware

exception_handlers = get_exception_handlers()

def on_startup() -> None:
    """
    Perform initialization tasks on application startup.
    """
    mq_client: MQClient = get_mq_client()
    mq_client.connect()

    mq_consumer = get_mq_consumer()
    mq_consumer.connect()
    mq_consumer.start_consuming()

def on_shutdown() -> None:
    """
    Perform cleanup tasks on application shutdown.
    """
    mq_client: MQClient = get_mq_client()
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
    exception_handlers=exception_handlers,
    lifespan=lifespan
)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.ALLOWED_CREDENTIALS,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
    expose_headers=[REQUEST_ID_HEADER],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(api_router, prefix=settings.API_V1_STR)
