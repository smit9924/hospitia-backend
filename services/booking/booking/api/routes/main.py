from fastapi import APIRouter

from booking.api.routes import organization, organization_type

# from auth.core.config import settings

api_router = APIRouter()
api_router.include_router(organization_type.router, prefix="/organization-type")
api_router.include_router(organization.router, prefix="/organization")


# if settings.ENVIRONMENT == "local":
#     api_router.include_router(private.router)
