from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.api.routes.main import api_router
from auth.core.config import settings
from auth.exceptions.registry import get_exception_handlers
from auth.messaging.base import MQClient
from auth.messaging.general import get_mq_client
from auth.middleware import REQUEST_ID_HEADER, RequestIdMiddleware

exception_handlers = get_exception_handlers()

def on_startup() -> None:
    """
    Perform initialization tasks on application startup.
    """
    mq_client: MQClient = get_mq_client()
    mq_client.connect()

def on_shutdown() -> None:
    """
    Perform cleanup tasks on application shutdown.
    """
    mq_client: MQClient = get_mq_client()
    mq_client.close()

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
