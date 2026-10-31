from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BeforeValidator, Field, StringConstraints

from .base_schemas import BaseSchema
from .organization_schemas import OrganizationReference


def _blank_to_none(value: object) -> object:
    """Treat a blank optional text value as "not provided"."""
    if isinstance(value, str) and not value.strip():
        return None
    return value


RoomAmenityName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]
# Optional; blank text is stored as null.
RoomAmenityDescription = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None,
    BeforeValidator(_blank_to_none),
]


class RoomAmenityUpsertRequest(BaseSchema):
    """
    Request payload for creating or updating a room amenity.

    When `guid` is omitted (or null), a new amenity is created; otherwise
    the amenity identified by `guid` is updated.

    `organization_guid` is read only when an admin creates an amenity:
    null creates a default amenity offered to every organization, a value
    creates a custom amenity of that organization. Owners and managers
    always create custom amenities of their active organization, and an
    amenity's scope never changes on update.
    """

    guid: UUID | None = None
    name: RoomAmenityName
    description: RoomAmenityDescription = None
    organization_guid: UUID | None = None


class RoomAmenityResponse(BaseSchema):
    guid: UUID
    name: str
    description: str | None
    is_default: bool
    # Owning organization of a custom amenity; null for a default amenity.
    organization: OrganizationReference | None
    created_at: datetime
    updated_at: datetime


class RoomAmenityOption(BaseSchema):
    """
    Compact room amenity offered for selection (e.g. room type amenity
    check boxes).
    """

    guid: UUID
    name: str
    description: str | None
    is_default: bool


class RoomAmenityListQueryParams(BaseSchema):
    """
    Query parameters for the paginated room amenity listing endpoint.
    `search_term` matches the amenity name.
    """

    search_term: str | None = None
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: Literal["name", "createdAt", "updatedAt"] = "name"
    sort_direction: Literal["asc", "desc"] = "asc"
    page_number: int = Field(default=1, ge=1)


class RoomAmenityListResponse(BaseSchema):
    items: list[RoomAmenityResponse]
    total_count: int
    page_number: int
    page_size: int


class RoomAmenitySelectableQueryParams(BaseSchema):
    """
    Query parameters for listing the amenities a room type may use.

    `organization_guid` is read only for admins, who are not tied to an
    organization: it selects whose custom amenities are offered next to
    the defaults (defaults only when omitted). Owners and managers always
    get the amenities of their active organization.
    """

    organization_guid: UUID | None = None
