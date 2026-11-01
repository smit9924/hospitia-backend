from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BeforeValidator, Field, StringConstraints

from booking.database.models.room import (
    ROOM_MAX_FLOOR,
    ROOM_MIN_FLOOR,
    ROOM_NOTES_MAX_LENGTH,
    ROOM_NUMBER_MAX_LENGTH,
    ROOM_NUMBER_PATTERN,
)
from booking.types.enums import RoomStatus
from booking.utils.text_utils import blank_text_to_none, strip_text

from .base_schemas import BaseSchema
from .organization_schemas import OrganizationReference
from .room_type_schemas import RoomTypeOption


class RoomAttributes(BaseSchema):
    """
    Room fields shared by the create and update requests.

    `room_number` is trimmed, then must be 1 to 20 letters, digits, "-" or
    "/" (e.g. "101", "A-12", "B2/04"). `floor` is a whole number from -500
    to 500: 0 is the ground floor and negative numbers are basement levels.
    """

    room_number: Annotated[
        str,
        BeforeValidator(strip_text),
        StringConstraints(min_length=1, max_length=ROOM_NUMBER_MAX_LENGTH, pattern=ROOM_NUMBER_PATTERN),
    ]
    floor: int = Field(strict=True, ge=ROOM_MIN_FLOOR, le=ROOM_MAX_FLOOR)
    room_type_guid: UUID
    # Optional; blank text is stored as null.
    notes: Annotated[
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=ROOM_NOTES_MAX_LENGTH)] | None,
        BeforeValidator(blank_text_to_none),
    ] = None


class RoomCreateRequest(RoomAttributes):
    """
    Request payload for creating a room.

    `organization_guid` is read only for admins, who must choose the
    organization; owners and managers always create rooms in their active
    organization. `status` defaults to "available".
    """

    organization_guid: UUID | None = None
    status: RoomStatus = RoomStatus.AVAILABLE


class RoomUpdateRequest(RoomAttributes):
    """
    Request payload for updating the room identified by `guid`.
    A room never moves to another organization.
    """

    guid: UUID
    status: RoomStatus


class RoomResponse(BaseSchema):
    """A room with its room type and organization."""

    guid: UUID
    room_number: str
    floor: int
    status: RoomStatus
    notes: str | None
    room_type: RoomTypeOption
    organization: OrganizationReference
    created_at: datetime
    updated_at: datetime


class RoomListQueryParams(BaseSchema):
    """
    Query parameters for the paginated room listing endpoint.
    `search_term` matches the room number.
    """

    search_term: str | None = None
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: Literal["roomNumber", "floor", "createdAt", "updatedAt"] = "roomNumber"
    sort_direction: Literal["asc", "desc"] = "asc"
    page_number: int = Field(default=1, ge=1)


class RoomListResponse(BaseSchema):
    items: list[RoomResponse]
    total_count: int
    page_number: int
    page_size: int
