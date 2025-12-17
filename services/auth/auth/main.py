

from fastapi import FastAPI

from auth.api.routes.main import api_router
from auth.core.config import settings
from auth.exceptions.registry import register_exception_handlers

app = FastAPI()

register_exception_handlers(app)

@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(api_router, prefix=settings.API_V1_STR)
