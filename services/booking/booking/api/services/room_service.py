"""
Business rules for rooms.

A room is an individual room (e.g. "101") of one organization and belongs
to one of that organization's room types. Its organization never changes.

- Admins manage the rooms of every active organization and choose the
  organization when creating one.
- Owners and managers manage the rooms of their active organization only;
  other organizations' rooms are reported as not found, so their existence
  is never revealed.

Room numbers are unique, case-insensitively, among the active rooms of one
organization.
"""

from uuid import UUID

from sqlmodel import Session

from booking.api.repositories.room_repository import (
    create_room as create_room_repo,
)
from booking.api.repositories.room_repository import (
    find_active_room_by_number,
    get_active_room_by_guid,
    list_rooms_page,
    soft_delete_room,
)
from booking.api.repositories.room_repository import (
    update_room as update_room_repo,
)
from booking.api.repositories.room_type_repository import get_active_room_type_by_guid
from booking.api.services.organization_service import (
    get_active_organization_or_raise,
    get_member_active_organization_id,
)
from booking.database.models.room import Room
from booking.exceptions.definitions.not_found_exceptions import RoomNotFoundException
from booking.exceptions.definitions.validation_exceptions import (
    RoomAlreadyExistsException,
    RoomOrganizationRequiredException,
    RoomTypeNotAvailableForRoomException,
)
from booking.schemas.organization_schemas import (
    OrganizationReference,
    OrganizationScopedActor,
)
from booking.schemas.room_schemas import (
    RoomCreateRequest,
    RoomListQueryParams,
    RoomListResponse,
    RoomResponse,
    RoomUpdateRequest,
)
from booking.schemas.room_type_schemas import RoomTypeOption


def _to_room_response(room: Room) -> RoomResponse:
    """Build the API response for a room.

    Parameters
    ----------
    room : Room
        Room with its organization and room type loaded.

    Returns
    -------
    RoomResponse
        The room with compact references to its room type and organization.
    """
    return RoomResponse(
        guid=room.guid,
        room_number=room.room_number,
        floor=room.floor,
        status=room.status,
        notes=room.notes,
        room_type=RoomTypeOption.model_validate(room.room_type, from_attributes=True),
        organization=OrganizationReference.model_validate(room.organization, from_attributes=True),
        created_at=room.created_at,
        updated_at=room.updated_at,
    )


def _get_visible_room_or_raise(*, session: Session, actor: OrganizationScopedActor, guid: UUID) -> Room:
    """Fetch an active room the actor may manage.

    Parameters
    ----------
    session : Session
        Active database session.
    actor : OrganizationScopedActor
        The caller and, for owners and managers, their active organization.
    guid : UUID
        Room GUID to look up.

    Returns
    -------
    Room
        The active room, with its organization and room type loaded.

    Raises
    ------
    RoomNotFoundException
        If the room does not exist, was deleted, belongs to a deleted
        organization, or belongs to another organization than an owner's or
        manager's active one.
    """
    room = get_active_room_by_guid(session=session, guid=guid)
    if room is None or not room.organization.is_active:
        raise RoomNotFoundException()
    if not actor.is_admin and room.organization_id != get_member_active_organization_id(actor):
        raise RoomNotFoundException()
    return room


def _resolve_organization_id_for_new_room(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    organization_guid: UUID | None,
) -> int:
    """Decide which organization a new room belongs to.

    Owners and managers create rooms in their active organization; admins
    must choose one.

    Parameters
    ----------
    session : Session
        Active database session.
    actor : OrganizationScopedActor
        The caller and, for owners and managers, their active organization.
    organization_guid : UUID | None
        Organization chosen by an admin; ignored for owners and managers.

    Returns
    -------
    int
        Internal ID of the organization.

    Raises
    ------
    RoomOrganizationRequiredException
        If an admin does not choose an organization.
    OrganizationNotFoundException
        If an admin chooses an organization that does not exist or is
        inactive.
    """
    if not actor.is_admin:
        return get_member_active_organization_id(actor)
    if organization_guid is None:
        raise RoomOrganizationRequiredException()
    return get_active_organization_or_raise(session=session, guid=organization_guid).id  # type: ignore[return-value]


def _resolve_room_type_id_for_organization(*, session: Session, room_type_guid: UUID, organization_id: int) -> int:
    """Return the internal ID of an active room type of the organization.

    Parameters
    ----------
    session : Session
        Active database session.
    room_type_guid : UUID
        Room type chosen for the room.
    organization_id : int
        Internal ID of the room's organization.

    Returns
    -------
    int
        Internal ID of the room type.

    Raises
    ------
    RoomTypeNotAvailableForRoomException
        If the room type does not exist, was deleted, or belongs to another
        organization.
    """
    room_type = get_active_room_type_by_guid(session=session, guid=room_type_guid)
    if room_type is None or room_type.organization_id != organization_id:
        raise RoomTypeNotAvailableForRoomException()
    return room_type.id  # type: ignore[return-value]


def _ensure_room_number_is_free(
    *,
    session: Session,
    organization_id: int,
    room_number: str,
    room_id_being_updated: int | None,
) -> None:
    """Make sure no other active room of the organization uses the number (case-insensitively).

    Parameters
    ----------
    session : Session
        Active database session.
    organization_id : int
        Internal ID of the room's organization.
    room_number : str
        Room number to check.
    room_id_being_updated : int | None
        Internal ID of the room being updated, so it does not conflict with
        itself; ``None`` on create.

    Returns
    -------
    None
        The number is free.

    Raises
    ------
    RoomAlreadyExistsException
        If another active room of the organization uses the number.
    """
    existing_room = find_active_room_by_number(session=session, organization_id=organization_id, room_number=room_number)
    if existing_room is not None and existing_room.id != room_id_being_updated:
        raise RoomAlreadyExistsException(message=f"Room {room_number} already exists in this organization.")


def create_room(*, session: Session, actor: OrganizationScopedActor, payload: RoomCreateRequest) -> RoomResponse:
    """Create a room.

    Admins create the room in `payload.organization_guid`; owners and
    managers create it in their active organization.

    Parameters
    ----------
    session : Session
        Active database session.
    actor : OrganizationScopedActor
        The caller and, for owners and managers, their active organization.
    payload : RoomCreateRequest
        Validated room fields.

    Returns
    -------
    RoomResponse
        The created room.

    Raises
    ------
    RoomOrganizationRequiredException
        If an admin does not choose an organization.
    OrganizationNotFoundException
        If an admin chooses a missing or inactive organization.
    RoomTypeNotAvailableForRoomException
        If the room type is not an active room type of the organization.
    RoomAlreadyExistsException
        If the room number is already used in the organization.
    """
    organization_id = _resolve_organization_id_for_new_room(
        session=session,
        actor=actor,
        organization_guid=payload.organization_guid,
    )
    room_type_id = _resolve_room_type_id_for_organization(
        session=session,
        room_type_guid=payload.room_type_guid,
        organization_id=organization_id,
    )
    _ensure_room_number_is_free(
        session=session,
        organization_id=organization_id,
        room_number=payload.room_number,
        room_id_being_updated=None,
    )
    room = create_room_repo(
        session=session,
        organization_id=organization_id,
        room_type_id=room_type_id,
        room_number=payload.room_number,
        floor=payload.floor,
        status=payload.status,
        notes=payload.notes,
        actor_id=actor.user_id,
    )
    return _to_room_response(room)


def update_room(*, session: Session, actor: OrganizationScopedActor, payload: RoomUpdateRequest) -> RoomResponse:
    """Update the room identified by `payload.guid`; its organization never changes.

    Parameters
    ----------
    session : Session
        Active database session.
    actor : OrganizationScopedActor
        The caller and, for owners and managers, their active organization.
    payload : RoomUpdateRequest
        GUID of the room and its new field values.

    Returns
    -------
    RoomResponse
        The updated room.

    Raises
    ------
    RoomNotFoundException
        If the room is missing or not visible to the actor.
    RoomTypeNotAvailableForRoomException
        If the room type is not an active room type of the room's
        organization.
    RoomAlreadyExistsException
        If another room of the organization uses the room number.
    """
    existing_room = _get_visible_room_or_raise(session=session, actor=actor, guid=payload.guid)
    room_type_id = _resolve_room_type_id_for_organization(
        session=session,
        room_type_guid=payload.room_type_guid,
        organization_id=existing_room.organization_id,
    )
    _ensure_room_number_is_free(
        session=session,
        organization_id=existing_room.organization_id,
        room_number=payload.room_number,
        room_id_being_updated=existing_room.id,
    )
    room = update_room_repo(
        session=session,
        room=existing_room,
        room_type_id=room_type_id,
        room_number=payload.room_number,
        floor=payload.floor,
        status=payload.status,
        notes=payload.notes,
        actor_id=actor.user_id,
    )
    return _to_room_response(room)


def get_room(*, session: Session, actor: OrganizationScopedActor, guid: UUID) -> RoomResponse:
    """Return one room the actor may manage.

    Parameters
    ----------
    session : Session
        Active database session.
    actor : OrganizationScopedActor
        The caller and, for owners and managers, their active organization.
    guid : UUID
        Room GUID to look up.

    Returns
    -------
    RoomResponse
        The room.

    Raises
    ------
    RoomNotFoundException
        If the room is missing, deleted, or not visible to the actor.
    """
    return _to_room_response(_get_visible_room_or_raise(session=session, actor=actor, guid=guid))


def delete_room(*, session: Session, actor: OrganizationScopedActor, guid: UUID) -> None:
    """Soft-delete a room the actor may manage.

    Parameters
    ----------
    session : Session
        Active database session.
    actor : OrganizationScopedActor
        The caller and, for owners and managers, their active organization.
    guid : UUID
        Room GUID to delete.

    Returns
    -------
    None
        The room is marked inactive.

    Raises
    ------
    RoomNotFoundException
        If the room is missing, deleted, or not visible to the actor.
    """
    room = _get_visible_room_or_raise(session=session, actor=actor, guid=guid)
    soft_delete_room(session=session, room=room, actor_id=actor.user_id)


def list_rooms(*, session: Session, actor: OrganizationScopedActor, query: RoomListQueryParams) -> RoomListResponse:
    """Return a paginated, sortable list of rooms, searchable by room number.

    Admins get the rooms of every active organization; owners and managers
    get the rooms of their active organization.

    Parameters
    ----------
    session : Session
        Active database session.
    actor : OrganizationScopedActor
        The caller and, for owners and managers, their active organization.
    query : RoomListQueryParams
        Search, sorting, and pagination options.

    Returns
    -------
    RoomListResponse
        The requested page of rooms and the total matching count.
    """
    organization_id = None if actor.is_admin else get_member_active_organization_id(actor)
    rooms, total_count = list_rooms_page(session=session, query=query, organization_id=organization_id)
    return RoomListResponse(
        items=[_to_room_response(room) for room in rooms],
        total_count=total_count,
        page_number=query.page_number,
        page_size=query.page_size,
    )
