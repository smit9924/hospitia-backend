from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship

from .base import SQLModel
from .mixins import AuditMixin
from .room_amenity import RoomAmenity
from .room_type import RoomType


class RoomTypeAmenityMapping(AuditMixin, SQLModel, table=True):
    """
    Database model linking a room type to one of its amenities.

    Attributes
    ----------
    id : int | None
        Primary key identifier for the mapping (internal use only).
    room_type_id : int
        Foreign key to `room_types.id`. Deletion of the room type is
        restricted (`ondelete="RESTRICT"`); room types are soft-deleted.
    room_amenity_id : int
        Foreign key to `room_amenities.id`. Deletion of the amenity is
        restricted; an amenity used by an active room type cannot be
        deleted at all.
    created_at, updated_at, created_by, updated_by
        Audit fields, see `AuditMixin`.

    Notes
    -----
    Unique on (room_type_id, room_amenity_id). Saving a room type replaces
    its mapping rows to match the selected amenities.
    """

    __tablename__ = "room_type_amenity_mappings"  # type: ignore
    __table_args__ = (
        UniqueConstraint("room_type_id", "room_amenity_id", name="uq_room_type_amenity_mappings_room_type_amenity"),
    )

    id: int | None = Field(default=None, primary_key=True, index=True)
    room_type_id: int = Field(foreign_key="room_types.id", nullable=False, index=True, ondelete="RESTRICT")
    room_amenity_id: int = Field(foreign_key="room_amenities.id", nullable=False, index=True, ondelete="RESTRICT")

    room_type: RoomType = Relationship()
    room_amenity: RoomAmenity = Relationship()


__all__ = [
    "RoomTypeAmenityMapping",
]
