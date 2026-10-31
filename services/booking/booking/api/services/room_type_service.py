"""
Business rules for room types.

A room type belongs to one organization for its whole life.

- Admins manage the room types of every active organization and choose
  the organization when creating one.
- Owners and managers manage the room types of their active organization
  only; other organizations' room types are reported as not found, so
  their existence is never revealed.

A room type may use the default amenities and the custom amenities of its
own organization, priced in any active currency unit.
"""

from collections.abc import Sequence
from uuid import UUID

from sqlmodel import Session

from booking.api.repositories.room_amenity_repository import (
    get_active_room_amenities_by_guids,
)
from booking.api.repositories.room_type_repository import (
    create_room_type,
    find_active_room_type_by_name,
    get_active_amenities_by_room_type_id,
    get_active_room_type_by_guid,
    list_room_types_page,
    soft_delete_room_type,
    update_room_type,
)
from booking.api.services.currency_unit_service import get_active_currency_unit_or_raise
from booking.api.services.organization_service import get_active_organization_or_raise
from booking.database.models.room_amenity import RoomAmenity
from booking.database.models.room_type import RoomType
from booking.exceptions.definitions.not_found_exceptions import (
    RoomTypeNotFoundException,
)
from booking.exceptions.definitions.validation_exceptions import (
    RoomTypeAlreadyExistsException,
    RoomTypeAmenityNotAvailableException,
    RoomTypeOrganizationRequiredException,
)
from booking.schemas.currency_unit_schemas import CurrencyUnitOption
from booking.schemas.organization_schemas import (
    OrganizationReference,
    OrganizationScopedActor,
)
from booking.schemas.room_amenity_schemas import RoomAmenityOption
from booking.schemas.room_type_schemas import (
    RoomTypeListQueryParams,
    RoomTypeListResponse,
    RoomTypeResponse,
    RoomTypeUpsertRequest,
)


def _member_organization_id(actor: OrganizationScopedActor) -> int:
    """Internal ID of an owner's or manager's active organization."""
    if actor.active_organization is None:
        # OrganizationScopedActorDep always resolves it for non-admins.
        raise RuntimeError("Organization member resolved without an active organization.")
    return actor.active_organization.id


def _build_room_type_response(room_type: RoomType, amenities: Sequence[RoomAmenity]) -> RoomTypeResponse:
    """Assemble the API view of a room type from its loaded relations and amenities."""
    return RoomTypeResponse(
        guid=room_type.guid,  # type: ignore[arg-type]
        name=room_type.name,
        description=room_type.description,
        capacity=room_type.capacity,
        cost_per_night=room_type.cost_per_night,
        currency_unit=CurrencyUnitOption.model_validate(room_type.currency_unit, from_attributes=True),
        amenities=[RoomAmenityOption.model_validate(amenity, from_attributes=True) for amenity in amenities],
        organization=OrganizationReference.model_validate(room_type.organization, from_attributes=True),
        created_at=room_type.created_at,
        updated_at=room_type.updated_at,
    )


def _to_room_type_response(*, session: Session, room_type: RoomType) -> RoomTypeResponse:
    """Build the response of one room type, loading its active amenities."""
    amenities_by_room_type_id = get_active_amenities_by_room_type_id(session=session, room_type_ids=[room_type.id])  # type: ignore[list-item]
    return _build_room_type_response(room_type, amenities_by_room_type_id.get(room_type.id, []))  # type: ignore[arg-type]


def _get_visible_room_type_or_raise(*, session: Session, actor: OrganizationScopedActor, guid: UUID) -> RoomType:
    """Fetch an active room type the actor may manage.

    Raises
    ------
    RoomTypeNotFoundException
        If the room type does not exist, was deleted, belongs to a deleted
        organization, or belongs to another organization than an owner's or
        manager's active one.
    """
    room_type = get_active_room_type_by_guid(session=session, guid=guid)
    if room_type is None or not room_type.organization.is_active:
        raise RoomTypeNotFoundException()
    if not actor.is_admin and room_type.organization_id != _member_organization_id(actor):
        raise RoomTypeNotFoundException()
    return room_type


def _resolve_organization_id_for_new_room_type(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    organization_guid: UUID | None,
) -> int:
    """Decide which organization a new room type belongs to.

    Raises
    ------
    RoomTypeOrganizationRequiredException
        If an admin does not choose an organization.
    OrganizationNotFoundException
        If an admin chooses an organization that does not exist or is
        inactive.
    """
    if not actor.is_admin:
        return _member_organization_id(actor)
    if organization_guid is None:
        raise RoomTypeOrganizationRequiredException()
    return get_active_organization_or_raise(session=session, guid=organization_guid).id  # type: ignore[return-value]


def _ensure_room_type_name_is_free(
    *,
    session: Session,
    organization_id: int,
    name: str,
    room_type_id_being_updated: int | None,
) -> None:
    """Make sure no other active room type of the organization uses the name.

    Raises
    ------
    RoomTypeAlreadyExistsException
        If the name is taken (case-insensitively).
    """
    name_owner = find_active_room_type_by_name(session=session, organization_id=organization_id, name=name)
    if name_owner is not None and name_owner.id != room_type_id_being_updated:
        raise RoomTypeAlreadyExistsException()


def _resolve_amenity_ids_available_to_organization(
    *,
    session: Session,
    organization_id: int,
    amenity_guids: Sequence[UUID],
) -> list[int]:
    """Translate selected amenity GUIDs into IDs, checking the organization may use each one.

    Raises
    ------
    RoomTypeAmenityNotAvailableException
        If an amenity is missing, deleted, or a custom amenity of another
        organization.
    """
    amenities = get_active_room_amenities_by_guids(session=session, guids=amenity_guids)
    available_amenities = [
        amenity for amenity in amenities if amenity.is_default or amenity.organization_id == organization_id
    ]
    if len(available_amenities) != len(amenity_guids):
        raise RoomTypeAmenityNotAvailableException()
    return [amenity.id for amenity in available_amenities]  # type: ignore[misc]


def upsert_room_type(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    payload: RoomTypeUpsertRequest,
) -> RoomTypeResponse:
    """Create a room type, or update the one identified by `payload.guid`.

    Parameters
    ----------
    session : Session
        Active database session.
    actor : OrganizationScopedActor
        The caller and, for owners and managers, their active organization.
    payload : RoomTypeUpsertRequest
        Validated room type fields.

    Returns
    -------
    RoomTypeResponse
        The saved room type with its currency and amenities.

    Raises
    ------
    RoomTypeNotFoundException
        On update, if the room type is missing or not visible to the actor.
    RoomTypeOrganizationRequiredException
        If an admin creates a room type without an organization.
    OrganizationNotFoundException
        If an admin's chosen organization is missing or inactive.
    CurrencyUnitNotFoundException
        If the currency unit is missing or deleted.
    RoomTypeAmenityNotAvailableException
        If an amenity is not available to the organization.
    RoomTypeAlreadyExistsException
        If the organization already has an active room type with this name.
    """
    existing_room_type = None
    if payload.guid is None:
        organization_id = _resolve_organization_id_for_new_room_type(
            session=session,
            actor=actor,
            organization_guid=payload.organization_guid,
        )
    else:
        existing_room_type = _get_visible_room_type_or_raise(session=session, actor=actor, guid=payload.guid)
        organization_id = existing_room_type.organization_id

    currency_unit = get_active_currency_unit_or_raise(session=session, guid=payload.currency_unit_guid)
    room_amenity_ids = _resolve_amenity_ids_available_to_organization(
        session=session,
        organization_id=organization_id,
        amenity_guids=payload.amenity_guids,
    )
    _ensure_room_type_name_is_free(
        session=session,
        organization_id=organization_id,
        name=payload.name,
        room_type_id_being_updated=existing_room_type.id if existing_room_type else None,
    )

    room_type_fields = {
        "name": payload.name,
        "description": payload.description,
        "capacity": payload.capacity,
        "cost_per_night": payload.cost_per_night,
        "currency_unit_id": currency_unit.id,
        "room_amenity_ids": room_amenity_ids,
        "actor_id": actor.user_id,
    }
    if existing_room_type is None:
        room_type = create_room_type(session=session, organization_id=organization_id, **room_type_fields)  # type: ignore[arg-type]
    else:
        room_type = update_room_type(session=session, room_type=existing_room_type, **room_type_fields)  # type: ignore[arg-type]

    return _to_room_type_response(session=session, room_type=room_type)


def get_room_type(*, session: Session, actor: OrganizationScopedActor, guid: UUID) -> RoomTypeResponse:
    """Return one room type the actor may manage.

    Raises
    ------
    RoomTypeNotFoundException
        If the room type is missing, deleted, or not visible to the actor.
    """
    room_type = _get_visible_room_type_or_raise(session=session, actor=actor, guid=guid)
    return _to_room_type_response(session=session, room_type=room_type)


def delete_room_type(*, session: Session, actor: OrganizationScopedActor, guid: UUID) -> None:
    """Soft-delete a room type the actor may manage.

    Raises
    ------
    RoomTypeNotFoundException
        If the room type is missing, deleted, or not visible to the actor.
    """
    room_type = _get_visible_room_type_or_raise(session=session, actor=actor, guid=guid)
    soft_delete_room_type(session=session, room_type=room_type, actor_id=actor.user_id)


def list_room_types(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    query: RoomTypeListQueryParams,
) -> RoomTypeListResponse:
    """Return a paginated, sortable, searchable list of the room types the actor may manage.

    Admins get the room types of every active organization; owners and
    managers get those of their active organization.
    """
    room_types, total_count = list_room_types_page(
        session=session,
        query=query,
        organization_id=None if actor.is_admin else _member_organization_id(actor),
    )
    amenities_by_room_type_id = get_active_amenities_by_room_type_id(
        session=session,
        room_type_ids=[room_type.id for room_type in room_types],  # type: ignore[misc]
    )
    return RoomTypeListResponse(
        items=[
            _build_room_type_response(room_type, amenities_by_room_type_id.get(room_type.id, []))  # type: ignore[arg-type]
            for room_type in room_types
        ],
        total_count=total_count,
        page_number=query.page_number,
        page_size=query.page_size,
    )
