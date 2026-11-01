"""
Business rules for room amenities.

An amenity is either a default (system-wide, managed by admins, offered to
every organization) or a custom amenity of one organization (managed by
its owners and managers, and by admins).

Visibility:
- Admins see every default amenity and every custom amenity of an active
  organization.
- Owners and managers see the defaults plus the custom amenities of their
  active organization. Other organizations' amenities are reported as not
  found, so their existence is never revealed.

Modification:
- Admins may edit or delete any amenity they can see.
- Owners and managers may edit or delete only their organization's custom
  amenities; defaults are read-only for them.
"""

from uuid import UUID

from sqlmodel import Session

from booking.api.repositories.room_amenity_repository import (
    create_room_amenity as create_room_amenity_repo,
)
from booking.api.repositories.room_amenity_repository import (
    find_active_room_amenity_by_name,
    get_active_room_amenity_by_guid,
    list_room_amenities_for_admin,
    list_room_amenities_for_organization,
    list_selectable_room_amenities,
    soft_delete_room_amenity,
)
from booking.api.repositories.room_amenity_repository import (
    update_room_amenity as update_room_amenity_repo,
)
from booking.api.repositories.room_type_repository import (
    has_active_room_types_using_amenity,
)
from booking.api.services.organization_service import (
    get_active_organization_or_raise,
    get_member_active_organization_id,
)
from booking.database.models.room_amenity import RoomAmenity
from booking.exceptions.definitions.not_found_exceptions import (
    RoomAmenityNotFoundException,
)
from booking.exceptions.definitions.security_exceptions import (
    RoomAmenityModificationForbiddenException,
)
from booking.exceptions.definitions.validation_exceptions import (
    RoomAmenityAlreadyExistsException,
    RoomAmenityInUseException,
)
from booking.schemas.organization_schemas import OrganizationScopedActor
from booking.schemas.room_amenity_schemas import (
    RoomAmenityCreateRequest,
    RoomAmenityListQueryParams,
    RoomAmenityListResponse,
    RoomAmenityOption,
    RoomAmenityResponse,
    RoomAmenityUpdateRequest,
)


def _is_visible_to_actor(room_amenity: RoomAmenity, actor: OrganizationScopedActor) -> bool:
    """Whether the actor may see the amenity (see the module docstring)."""
    if room_amenity.is_default:
        return True
    if actor.is_admin:
        # Custom amenities of a deleted organization are hidden from admins too.
        return room_amenity.organization is not None and room_amenity.organization.is_active
    return room_amenity.organization_id == get_member_active_organization_id(actor)


def _get_visible_room_amenity_or_raise(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    guid: UUID,
) -> RoomAmenity:
    """Fetch an active amenity the actor may see.

    Raises
    ------
    RoomAmenityNotFoundException
        If the amenity does not exist, was deleted, or is not visible to
        the actor.
    """
    room_amenity = get_active_room_amenity_by_guid(session=session, guid=guid)
    if room_amenity is None or not _is_visible_to_actor(room_amenity, actor):
        raise RoomAmenityNotFoundException()
    return room_amenity


def _ensure_actor_can_modify(actor: OrganizationScopedActor, room_amenity: RoomAmenity) -> None:
    """Block owners and managers from changing default amenities.

    Raises
    ------
    RoomAmenityModificationForbiddenException
        If a non-admin targets a default amenity.
    """
    if room_amenity.is_default and not actor.is_admin:
        raise RoomAmenityModificationForbiddenException()


def _resolve_target_organization_id(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    organization_guid: UUID | None,
) -> int | None:
    """Decide which organization a request acts on; ``None`` means the defaults only.

    Owners and managers always act on their active organization. Admins act
    on the organization chosen with `organization_guid`, or on the default
    amenities when they choose none. Used both to place a new amenity and
    to decide whose custom amenities are selectable for a room type.

    Raises
    ------
    OrganizationNotFoundException
        If an admin chooses an organization that does not exist or is
        inactive.
    """
    if not actor.is_admin:
        return get_member_active_organization_id(actor)
    if organization_guid is None:
        return None
    return get_active_organization_or_raise(session=session, guid=organization_guid).id


def _ensure_name_is_free_among_default_amenities(
    *,
    session: Session,
    name: str,
    room_amenity_id_being_updated: int | None,
    conflict_message: str | None = None,
) -> None:
    """Make sure no other active default amenity uses the name (case-insensitively).

    Parameters
    ----------
    session : Session
        Active database session.
    name : str
        Amenity name to check.
    room_amenity_id_being_updated : int | None
        Internal ID of the amenity being updated, so it does not conflict
        with itself; ``None`` on create.
    conflict_message : str | None
        Error message to use instead of the default one.

    Raises
    ------
    RoomAmenityAlreadyExistsException
        If a default amenity already uses the name.
    """
    name_owner = find_active_room_amenity_by_name(session=session, name=name, organization_id=None)
    if name_owner is not None and name_owner.id != room_amenity_id_being_updated:
        if conflict_message is None:
            raise RoomAmenityAlreadyExistsException()
        raise RoomAmenityAlreadyExistsException(message=conflict_message)


def _ensure_name_is_free_among_organization_amenities(
    *,
    session: Session,
    name: str,
    organization_id: int,
    room_amenity_id_being_updated: int | None,
) -> None:
    """Make sure no other active custom amenity of the organization uses the name (case-insensitively).

    Parameters
    ----------
    session : Session
        Active database session.
    name : str
        Amenity name to check.
    organization_id : int
        Internal ID of the organization whose custom amenities are checked.
    room_amenity_id_being_updated : int | None
        Internal ID of the amenity being updated, so it does not conflict
        with itself; ``None`` on create.

    Raises
    ------
    RoomAmenityAlreadyExistsException
        If a custom amenity of the organization already uses the name.
    """
    name_owner = find_active_room_amenity_by_name(session=session, name=name, organization_id=organization_id)
    if name_owner is not None and name_owner.id != room_amenity_id_being_updated:
        raise RoomAmenityAlreadyExistsException()


def _ensure_room_amenity_name_is_free(
    *,
    session: Session,
    name: str,
    organization_id: int | None,
    room_amenity_id_being_updated: int | None,
) -> None:
    """Make sure the name is free where the amenity is shown.

    - A default amenity (``organization_id`` is ``None``) is checked against
      the other defaults.
    - A custom amenity is checked against its organization's custom
      amenities, and against the defaults too: the organization sees both
      side by side, so it must never get two amenities with the same name.

    Raises
    ------
    RoomAmenityAlreadyExistsException
        If the name is taken (case-insensitively).
    """
    if organization_id is None:
        _ensure_name_is_free_among_default_amenities(
            session=session,
            name=name,
            room_amenity_id_being_updated=room_amenity_id_being_updated,
        )
        return

    _ensure_name_is_free_among_organization_amenities(
        session=session,
        name=name,
        organization_id=organization_id,
        room_amenity_id_being_updated=room_amenity_id_being_updated,
    )
    _ensure_name_is_free_among_default_amenities(
        session=session,
        name=name,
        # A custom amenity is never a default, so nothing to exclude here.
        room_amenity_id_being_updated=None,
        conflict_message="A default room amenity with this name already exists.",
    )


def create_room_amenity(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    payload: RoomAmenityCreateRequest,
) -> RoomAmenityResponse:
    """Create a room amenity.

    Admins create a default amenity, or a custom amenity of
    `payload.organization_guid`; owners and managers create a custom
    amenity of their active organization.

    Parameters
    ----------
    session : Session
        Active database session.
    actor : OrganizationScopedActor
        The caller and, for owners and managers, their active organization.
    payload : RoomAmenityCreateRequest
        Validated amenity fields.

    Returns
    -------
    RoomAmenityResponse
        The created amenity.

    Raises
    ------
    OrganizationNotFoundException
        If an admin creates an amenity for a missing or inactive organization.
    RoomAmenityAlreadyExistsException
        If the name is already used in the amenity's scope.
    """
    organization_id = _resolve_target_organization_id(
        session=session,
        actor=actor,
        organization_guid=payload.organization_guid,
    )
    _ensure_room_amenity_name_is_free(
        session=session,
        name=payload.name,
        organization_id=organization_id,
        room_amenity_id_being_updated=None,
    )
    room_amenity = create_room_amenity_repo(
        session=session,
        name=payload.name,
        description=payload.description,
        organization_id=organization_id,
        actor_id=actor.user_id,
    )
    return RoomAmenityResponse.model_validate(room_amenity, from_attributes=True)


def update_room_amenity(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    payload: RoomAmenityUpdateRequest,
) -> RoomAmenityResponse:
    """Update the name and description of the room amenity identified by `payload.guid`.

    Parameters
    ----------
    session : Session
        Active database session.
    actor : OrganizationScopedActor
        The caller and, for owners and managers, their active organization.
    payload : RoomAmenityUpdateRequest
        GUID of the amenity and its new field values.

    Returns
    -------
    RoomAmenityResponse
        The updated amenity.

    Raises
    ------
    RoomAmenityNotFoundException
        If the amenity is missing or not visible to the actor.
    RoomAmenityModificationForbiddenException
        If an owner or manager tries to update a default amenity.
    RoomAmenityAlreadyExistsException
        If the name is already used in the amenity's scope.
    """
    existing_room_amenity = _get_visible_room_amenity_or_raise(session=session, actor=actor, guid=payload.guid)
    _ensure_actor_can_modify(actor, existing_room_amenity)
    _ensure_room_amenity_name_is_free(
        session=session,
        name=payload.name,
        organization_id=existing_room_amenity.organization_id,
        room_amenity_id_being_updated=existing_room_amenity.id,
    )
    room_amenity = update_room_amenity_repo(
        session=session,
        room_amenity=existing_room_amenity,
        name=payload.name,
        description=payload.description,
        actor_id=actor.user_id,
    )
    return RoomAmenityResponse.model_validate(room_amenity, from_attributes=True)


def get_room_amenity(*, session: Session, actor: OrganizationScopedActor, guid: UUID) -> RoomAmenityResponse:
    """Return one amenity visible to the actor.

    Raises
    ------
    RoomAmenityNotFoundException
        If the amenity is missing, deleted, or not visible to the actor.
    """
    room_amenity = _get_visible_room_amenity_or_raise(session=session, actor=actor, guid=guid)
    return RoomAmenityResponse.model_validate(room_amenity, from_attributes=True)


def ensure_room_amenity_is_not_in_use(*, session: Session, room_amenity_id: int) -> None:
    """Block deleting an amenity that active records still use.

    Add one check per referencing table here as new tables reference
    room amenities.

    Parameters
    ----------
    session : Session
        Active database session.
    room_amenity_id : int
        Internal ID of the amenity to validate.

    Raises
    ------
    RoomAmenityInUseException
        If an active room type lists the amenity.
    """
    if has_active_room_types_using_amenity(session=session, room_amenity_id=room_amenity_id):
        raise RoomAmenityInUseException(message="Cannot delete a room amenity that active room types use.")


def delete_room_amenity(*, session: Session, actor: OrganizationScopedActor, guid: UUID) -> None:
    """Soft-delete an amenity the actor may modify and nothing active uses.

    Raises
    ------
    RoomAmenityNotFoundException
        If the amenity is missing, deleted, or not visible to the actor.
    RoomAmenityModificationForbiddenException
        If an owner or manager tries to delete a default amenity.
    RoomAmenityInUseException
        If an active record still uses the amenity.
    """
    room_amenity = _get_visible_room_amenity_or_raise(session=session, actor=actor, guid=guid)
    _ensure_actor_can_modify(actor, room_amenity)
    ensure_room_amenity_is_not_in_use(session=session, room_amenity_id=room_amenity.id)
    soft_delete_room_amenity(session=session, room_amenity=room_amenity, actor_id=actor.user_id)


def list_room_amenities(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    query: RoomAmenityListQueryParams,
) -> RoomAmenityListResponse:
    """Return a paginated, sortable, searchable list of the amenities visible to the actor."""
    if actor.is_admin:
        return list_room_amenities_for_admin(session=session, query=query)
    return list_room_amenities_for_organization(
        session=session,
        query=query,
        organization_id=get_member_active_organization_id(actor),
    )


def list_selectable_room_amenity_options(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    organization_guid: UUID | None,
) -> list[RoomAmenityOption]:
    """Return the amenities a room type of the organization may use, ordered by name.

    Raises
    ------
    OrganizationNotFoundException
        If an admin chooses an organization that does not exist or is
        inactive.
    """
    organization_id = _resolve_target_organization_id(
        session=session,
        actor=actor,
        organization_guid=organization_guid,
    )
    return [
        RoomAmenityOption.model_validate(room_amenity, from_attributes=True)
        for room_amenity in list_selectable_room_amenities(session=session, organization_id=organization_id)
    ]
