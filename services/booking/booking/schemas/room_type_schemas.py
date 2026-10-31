from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BeforeValidator, Field, StringConstraints, field_validator

from booking.database.models.room_type import (
    ROOM_TYPE_MAX_CAPACITY,
    ROOM_TYPE_MAX_COST_PER_NIGHT,
    ROOM_TYPE_MIN_CAPACITY,
)

from .base_schemas import BaseSchema
from .currency_unit_schemas import CurrencyUnitOption
from .organization_schemas import OrganizationReference
from .room_amenity_schemas import RoomAmenityOption

# A room type cannot list more amenities than this in one request.
MAX_AMENITIES_PER_ROOM_TYPE = 100


def _blank_to_none(value: object) -> object:
    """Treat a blank optional text value as "not provided"."""
    if isinstance(value, str) and not value.strip():
        return None
    return value


RoomTypeName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]
# Optional; blank text is stored as null.
RoomTypeDescription = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None,
    BeforeValidator(_blank_to_none),
]


class RoomTypeUpsertRequest(BaseSchema):
    """
    Request payload for creating or updating a room type.

    When `guid` is omitted (or null), a new room type is created; otherwise
    the room type identified by `guid` is updated.

    `organization_guid` is read only when an admin creates a room type, and
    is then required. Owners and managers always create room types in their
    active organization, and a room type never moves to another
    organization.

    `cost_per_night` accepts at most two decimal places (e.g. 1500 or
    1499.50) and may be 0 for free stays. `amenity_guids` replaces the room
    type's amenities; duplicates are ignored.
    """

    guid: UUID | None = None
    organization_guid: UUID | None = None
    name: RoomTypeName
    description: RoomTypeDescription = None
    capacity: int = Field(strict=True, ge=ROOM_TYPE_MIN_CAPACITY, le=ROOM_TYPE_MAX_CAPACITY)
    cost_per_night: Decimal = Field(ge=0, le=ROOM_TYPE_MAX_COST_PER_NIGHT, decimal_places=2, allow_inf_nan=False)
    currency_unit_guid: UUID
    amenity_guids: list[UUID] = Field(default_factory=list, max_length=MAX_AMENITIES_PER_ROOM_TYPE)

    @field_validator("amenity_guids")
    @classmethod
    def remove_duplicate_amenity_guids(cls, amenity_guids: list[UUID]) -> list[UUID]:
        """Keep the first occurrence of each amenity GUID, preserving order."""
        return list(dict.fromkeys(amenity_guids))


class RoomTypeResponse(BaseSchema):
    """
    A room type with its currency and amenities.

    `cost_per_night` is serialized as a decimal string (e.g. "1500.00") so
    no precision is lost in JSON.
    """

    guid: UUID
    name: str
    description: str | None
    capacity: int
    cost_per_night: Decimal
    currency_unit: CurrencyUnitOption
    amenities: list[RoomAmenityOption]
    organization: OrganizationReference
    created_at: datetime
    updated_at: datetime


class RoomTypeListQueryParams(BaseSchema):
    """
    Query parameters for the paginated room type listing endpoint.
    `search_term` matches the room type name.
    """

    search_term: str | None = None
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: Literal["name", "capacity", "costPerNight", "createdAt", "updatedAt"] = "name"
    sort_direction: Literal["asc", "desc"] = "asc"
    page_number: int = Field(default=1, ge=1)


class RoomTypeListResponse(BaseSchema):
    items: list[RoomTypeResponse]
    total_count: int
    page_number: int
    page_size: int
