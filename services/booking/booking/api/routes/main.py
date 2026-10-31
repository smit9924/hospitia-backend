from fastapi import APIRouter

from booking.api.routes import (
    currency_unit,
    organization,
    organization_type,
    room_amenity,
    room_type,
)

# from auth.core.config import settings

api_router = APIRouter()
api_router.include_router(organization_type.router, prefix="/organization-type")
api_router.include_router(organization.router, prefix="/organization")
api_router.include_router(currency_unit.router, prefix="/currency-unit")
api_router.include_router(room_amenity.router, prefix="/room-amenity")
api_router.include_router(room_type.router, prefix="/room-type")


# if settings.ENVIRONMENT == "local":
#     api_router.include_router(private.router)
