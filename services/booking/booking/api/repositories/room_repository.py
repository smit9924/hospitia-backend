from uuid import UUID

from sqlalchemy import ColumnElement
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, func, select

from booking.database.models.organization import Organization
from booking.database.models.room import Room
from booking.schemas.room_schemas import RoomListQueryParams
from booking.types.enums import RoomStatus

_SORT_COLUMNS = {
    "roomNumber": Room.room_number,
    "floor": Room.floor,
    "createdAt": Room.created_at,
    "updatedAt": Room.updated_at,
}

_IS_ACTIVE = Room.is_active == True  # noqa: E712


def get_active_room_by_guid(*, session: Session, guid: UUID | str) -> Room | None:
    """Fetch an active room, with its organization and room type, by GUID.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    guid : UUID | str
        Room GUID to look up.

    Returns
    -------
    Room | None
        Matching active room, or ``None`` if it does not exist or was
        deleted.
    """
    return session.exec(
        select(Room)
        .options(selectinload(Room.organization), selectinload(Room.room_type))  # type: ignore[arg-type]
        .where(Room.guid == guid, _IS_ACTIVE)
    ).first()


def find_active_room_by_number(*, session: Session, organization_id: int, room_number: str) -> Room | None:
    """Find an active room of the organization with the same number, ignoring case.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    organization_id : int
        Internal ID of the organization.
    room_number : str
        Room number to look for.

    Returns
    -------
    Room | None
        The room using that number, or ``None``.
    """
    return session.exec(
        select(Room).where(
            Room.organization_id == organization_id,
            func.lower(Room.room_number) == room_number.lower(),
            _IS_ACTIVE,
        )
    ).first()


def create_room(
    *,
    session: Session,
    organization_id: int,
    room_type_id: int,
    room_number: str,
    floor: int,
    status: RoomStatus,
    notes: str | None,
    actor_id: int | None,
) -> Room:
    """Create and commit a room.

    Parameters
    ----------
    session : Session
        Active database session used to persist the room.
    organization_id : int
        Internal ID of the owning organization.
    room_type_id : int
        Internal ID of the room type (of the same organization).
    room_number : str
        Room number, already validated.
    floor : int
        Floor from -500 to 500.
    status : RoomStatus
        Operational status.
    notes : str | None
        Optional notes.
    actor_id : int | None
        Internal ID of the user performing the operation, if available.

    Returns
    -------
    Room
        Newly created room with its organization and room type loaded.
    """
    room = Room(
        organization_id=organization_id,
        room_type_id=room_type_id,
        room_number=room_number,
        floor=floor,
        status=status,
        notes=notes,
        # Pylance does not recognize inherited properties from AuditMixin.
        created_by=actor_id,  # type: ignore[call-arg]
        updated_by=actor_id,  # type: ignore[call-arg]
    )
    session.add(room)
    session.commit()
    session.refresh(room)
    return room


def update_room(
    *,
    session: Session,
    room: Room,
    room_type_id: int,
    room_number: str,
    floor: int,
    status: RoomStatus,
    notes: str | None,
    actor_id: int | None,
) -> Room:
    """Update and commit a room's editable fields.

    The room's organization never changes.

    Parameters
    ----------
    session : Session
        Active database session used to persist the update.
    room : Room
        Room instance to update.
    room_type_id : int
        Internal ID of the new room type (of the same organization).
    room_number : str
        Replacement room number, already validated.
    floor : int
        Replacement floor.
    status : RoomStatus
        Replacement status.
    notes : str | None
        Replacement notes.
    actor_id : int | None
        Internal ID of the user performing the update, if available.

    Returns
    -------
    Room
        Updated and refreshed room.
    """
    room.room_type_id = room_type_id
    room.room_number = room_number
    room.floor = floor
    room.status = status
    room.notes = notes
    room.updated_by = actor_id

    session.add(room)
    session.commit()
    session.refresh(room)
    return room


def soft_delete_room(*, session: Session, room: Room, actor_id: int | None) -> None:
    """Soft-delete a room by marking it inactive.

    Parameters
    ----------
    session : Session
        Active database session used to commit the change.
    room : Room
        Room to deactivate.
    actor_id : int | None
        Internal ID of the user performing the deletion, if available.

    Returns
    -------
    None
        The change is committed successfully.

    Raises
    ------
    SQLAlchemyError
        If the change cannot be committed.
    """
    room.is_active = False
    room.updated_by = actor_id
    session.add(room)
    session.commit()


def list_rooms_page(
    *,
    session: Session,
    query: RoomListQueryParams,
    organization_id: int | None,
) -> tuple[list[Room], int]:
    """List active rooms with room number search, sorting, and pagination.

    Parameters
    ----------
    session : Session
        Active database session used to execute the queries.
    query : RoomListQueryParams
        Search, sorting, and pagination options.
    organization_id : int | None
        Restricts the list to one organization; ``None`` lists the rooms of
        every active organization (admin view).

    Returns
    -------
    tuple[list[Room], int]
        The page of rooms (organization and room type loaded) and the total
        matching count.

    Raises
    ------
    KeyError
        If ``query.sort_by`` is not in the supported sort-column map.
    """
    filters: list[ColumnElement[bool]] = [_IS_ACTIVE]
    if organization_id is None:
        active_organization_ids = select(Organization.id).where(Organization.is_active == True)  # noqa: E712
        filters.append(col(Room.organization_id).in_(active_organization_ids))
    else:
        filters.append(Room.organization_id == organization_id)

    search_term = (query.search_term or "").strip()
    if search_term:
        filters.append(col(Room.room_number).ilike(f"%{search_term}%"))

    statement = (
        select(Room)
        .options(selectinload(Room.organization), selectinload(Room.room_type))  # type: ignore[arg-type]
        .where(*filters)
    )
    sort_column = col(_SORT_COLUMNS[query.sort_by])
    # Secondary order by room number keeps pages stable when sorting by floor or date.
    tie_breaker = func.lower(Room.room_number)
    if query.sort_direction == "desc":
        statement = statement.order_by(sort_column.desc(), tie_breaker.desc())
    else:
        statement = statement.order_by(sort_column.asc(), tie_breaker.asc())

    offset = (query.page_number - 1) * query.page_size
    statement = statement.offset(offset).limit(query.page_size)
    count_statement = select(func.count()).select_from(Room).where(*filters)

    return list(session.exec(statement).all()), session.exec(count_statement).one()


def has_active_rooms_for_room_type(*, session: Session, room_type_id: int) -> bool:
    """Check whether an active room still uses the room type.

    Parameters
    ----------
    session : Session
        Active database session used to execute the count query.
    room_type_id : int
        Internal ID of the room type to check.

    Returns
    -------
    bool
        ``True`` when at least one active room uses the room type;
        otherwise ``False``.
    """
    statement = select(func.count()).select_from(Room).where(Room.room_type_id == room_type_id, _IS_ACTIVE)
    return session.exec(statement).one() > 0


def has_active_rooms_in_organization(*, session: Session, organization_id: int) -> bool:
    """Check whether the organization still has an active room.

    Parameters
    ----------
    session : Session
        Active database session used to execute the count query.
    organization_id : int
        Internal ID of the organization to check.

    Returns
    -------
    bool
        ``True`` when the organization has at least one active room;
        otherwise ``False``.
    """
    statement = select(func.count()).select_from(Room).where(Room.organization_id == organization_id, _IS_ACTIVE)
    return session.exec(statement).one() > 0


def list_active_rooms_of_organization(*, session: Session, organization_id: int) -> list[Room]:
    """List every active room of one organization for the floor chart.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    organization_id : int
        Internal ID of the organization.

    Returns
    -------
    list[Room]
        Active rooms with their room type loaded, ordered by floor from the
        top floor down, then by room number (case-insensitive).
    """
    return list(
        session.exec(
            select(Room)
            .options(selectinload(Room.room_type))  # type: ignore[arg-type]
            .where(Room.organization_id == organization_id, _IS_ACTIVE)
            .order_by(col(Room.floor).desc(), func.lower(Room.room_number))
        ).all()
    )


def update_room_status(*, session: Session, room: Room, status: RoomStatus, actor_id: int | None) -> Room:
    """Update and commit only the status of a room.

    Parameters
    ----------
    session : Session
        Active database session used to persist the update.
    room : Room
        Room instance to update.
    status : RoomStatus
        New operational status.
    actor_id : int | None
        Internal ID of the user performing the update, if available.

    Returns
    -------
    Room
        Updated and refreshed room.
    """
    room.status = status
    room.updated_by = actor_id
    session.add(room)
    session.commit()
    session.refresh(room)
    return room
