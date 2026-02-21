from fastapi import FastAPI

from auth.api.routes.main import api_router
from auth.core.config import settings
from auth.exceptions.registry import get_exception_handlers

exception_handlers = get_exception_handlers()


app = FastAPI(
    exception_handlers=exception_handlers,
)

@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(api_router, prefix=settings.API_V1_STR)
