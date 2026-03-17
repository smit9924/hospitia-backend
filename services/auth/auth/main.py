from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.api.routes.main import api_router
from auth.core.config import settings
from auth.exceptions.registry import get_exception_handlers

exception_handlers = get_exception_handlers()

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Lifespan function to handle startup and shutdown events."""
#     # Perform any startup tasks here (e.g., database connection, cache setup)
#     yield
#     RabbitMQClient.close_connection()  # Ensure RabbitMQ connection is closed on shutdown


app = FastAPI(
    exception_handlers=exception_handlers,
    # lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.ALLOWED_CREDENTIALS,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(api_router, prefix=settings.API_V1_STR)
