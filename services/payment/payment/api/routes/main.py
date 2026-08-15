from fastapi import APIRouter

from payment.api.routes import login

# from auth.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router, prefix="/login")


# if settings.ENVIRONMENT == "local":
#     api_router.include_router(private.router)
