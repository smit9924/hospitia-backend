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
from booking.utils.text_utils import blank_text_to_none

from .base_schemas import BaseSchema
from .currency_unit_schemas import CurrencyUnitOption
from .organization_schemas import OrganizationReference
from .room_amenity_schemas import RoomAmenityOption

# A room type cannot list more amenities than this in one request.
MAX_AMENITIES_PER_ROOM_TYPE = 100


class RoomTypeAttributes(BaseSchema):
    """
    Room type fields shared by the create and update requests.

    `cost_per_night` accepts at most two decimal places (e.g. 1500 or
    1499.50) and may be 0 for free stays. `amenity_guids` is the full list
    of the room type's amenities; duplicates are ignored.
    """

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    # Optional; blank text is stored as null.
    description: Annotated[
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None,
        BeforeValidator(blank_text_to_none),
    ] = None
    capacity: int = Field(strict=True, ge=ROOM_TYPE_MIN_CAPACITY, le=ROOM_TYPE_MAX_CAPACITY)
    cost_per_night: Decimal = Field(ge=0, le=ROOM_TYPE_MAX_COST_PER_NIGHT, decimal_places=2, allow_inf_nan=False)
    currency_unit_guid: UUID
    amenity_guids: list[UUID] = Field(default_factory=list, max_length=MAX_AMENITIES_PER_ROOM_TYPE)

    @field_validator("amenity_guids")
    @classmethod
    def remove_duplicate_amenity_guids(cls, amenity_guids: list[UUID]) -> list[UUID]:
        """Keep the first occurrence of each amenity GUID, preserving order."""
        return list(dict.fromkeys(amenity_guids))


class RoomTypeCreateRequest(RoomTypeAttributes):
    """
    Request payload for creating a room type.

    `organization_guid` is read only for admins, who must choose the
    organization; owners and managers always create room types in their
    active organization.
    """

    organization_guid: UUID | None = None


class RoomTypeUpdateRequest(RoomTypeAttributes):
    """
    Request payload for updating the room type identified by `guid`.
    A room type never moves to another organization.
    """

    guid: UUID


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


class RoomTypeOption(BaseSchema):
    """
    Compact room type offered for selection (e.g. the room form's room type
    drop-down) and embedded in room responses.
    """

    guid: UUID
    name: str


class RoomTypeOptionsQueryParams(BaseSchema):
    """
    Query parameters for listing the room types a room of the organization
    may use.

    `organization_guid` is read only for admins, who are not tied to an
    organization; owners and managers always get their active
    organization's room types.
    """

    organization_guid: UUID | None = None


class RoomTypeListResponse(BaseSchema):
    items: list[RoomTypeResponse]
    total_count: int
    page_number: int
    page_size: int
