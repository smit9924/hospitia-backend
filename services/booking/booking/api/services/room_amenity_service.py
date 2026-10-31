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
    create_room_amenity,
    find_active_room_amenity_by_name,
    get_active_room_amenity_by_guid,
    list_room_amenities_for_admin,
    list_room_amenities_for_organization,
    list_selectable_room_amenities,
    soft_delete_room_amenity,
    update_room_amenity,
)
from booking.api.repositories.room_type_repository import (
    has_active_room_types_using_amenity,
)
from booking.api.services.organization_service import get_active_organization_or_raise
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
    RoomAmenityListQueryParams,
    RoomAmenityListResponse,
    RoomAmenityOption,
    RoomAmenityResponse,
    RoomAmenityUpsertRequest,
)


def _member_organization_id(actor: OrganizationScopedActor) -> int:
    """Internal ID of an owner's or manager's active organization."""
    if actor.active_organization is None:
        # OrganizationScopedActorDep always resolves it for non-admins.
        raise RuntimeError("Organization member resolved without an active organization.")
    return actor.active_organization.id


def _is_visible_to_actor(room_amenity: RoomAmenity, actor: OrganizationScopedActor) -> bool:
    """Whether the actor may see the amenity (see the module docstring)."""
    if room_amenity.is_default:
        return True
    if actor.is_admin:
        # Custom amenities of a deleted organization are hidden from admins too.
        return room_amenity.organization is not None and room_amenity.organization.is_active
    return room_amenity.organization_id == _member_organization_id(actor)


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


def _resolve_organization_id_for_new_amenity(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    organization_guid: UUID | None,
) -> int | None:
    """Decide which scope a new amenity belongs to.

    Admins create a default amenity (no `organization_guid`) or a custom
    amenity of the chosen active organization. Owners and managers always
    create custom amenities of their active organization.

    Raises
    ------
    OrganizationNotFoundException
        If an admin chooses an organization that does not exist or is
        inactive.
    """
    if not actor.is_admin:
        return _member_organization_id(actor)
    if organization_guid is None:
        return None
    return get_active_organization_or_raise(session=session, guid=organization_guid).id


def _ensure_room_amenity_name_is_free(
    *,
    session: Session,
    name: str,
    organization_id: int | None,
    room_amenity_id_being_updated: int | None,
) -> None:
    """Make sure the name is not already used in the amenity's scope.

    A default name must be unique among defaults. A custom name must be
    unique within its organization and must not repeat a default name, so
    an organization never sees two amenities with the same name.

    Raises
    ------
    RoomAmenityAlreadyExistsException
        If the name is taken (case-insensitively).
    """
    scopes_to_check: list[int | None] = [organization_id]
    if organization_id is not None:
        scopes_to_check.append(None)

    for scope_organization_id in scopes_to_check:
        name_owner = find_active_room_amenity_by_name(
            session=session,
            name=name,
            organization_id=scope_organization_id,
        )
        if name_owner is not None and name_owner.id != room_amenity_id_being_updated:
            if scope_organization_id is None and organization_id is not None:
                raise RoomAmenityAlreadyExistsException(message="A default room amenity with this name already exists.")
            raise RoomAmenityAlreadyExistsException()


def upsert_room_amenity(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    payload: RoomAmenityUpsertRequest,
) -> RoomAmenityResponse:
    """Create a room amenity, or update the one identified by `payload.guid`.

    Parameters
    ----------
    session : Session
        Active database session.
    actor : OrganizationScopedActor
        The caller and, for owners and managers, their active organization.
    payload : RoomAmenityUpsertRequest
        Validated amenity fields.

    Returns
    -------
    RoomAmenityResponse
        The saved amenity.

    Raises
    ------
    RoomAmenityNotFoundException
        On update, if the amenity is missing or not visible to the actor.
    RoomAmenityModificationForbiddenException
        If an owner or manager tries to update a default amenity.
    OrganizationNotFoundException
        If an admin creates an amenity for a missing or inactive organization.
    RoomAmenityAlreadyExistsException
        If the name is already used in the amenity's scope.
    """
    if payload.guid is None:
        organization_id = _resolve_organization_id_for_new_amenity(
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
        room_amenity = create_room_amenity(
            session=session,
            name=payload.name,
            description=payload.description,
            organization_id=organization_id,
            actor_id=actor.user_id,
        )
    else:
        existing_room_amenity = _get_visible_room_amenity_or_raise(session=session, actor=actor, guid=payload.guid)
        _ensure_actor_can_modify(actor, existing_room_amenity)
        _ensure_room_amenity_name_is_free(
            session=session,
            name=payload.name,
            organization_id=existing_room_amenity.organization_id,
            room_amenity_id_being_updated=existing_room_amenity.id,
        )
        room_amenity = update_room_amenity(
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
        organization_id=_member_organization_id(actor),
    )


def resolve_selectable_organization_id(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    organization_guid: UUID | None,
) -> int | None:
    """Decide whose custom amenities are selectable next to the defaults.

    Owners and managers always get their active organization. Admins choose
    an organization with `organization_guid` (defaults only when omitted).

    Raises
    ------
    OrganizationNotFoundException
        If an admin chooses an organization that does not exist or is
        inactive.
    """
    if not actor.is_admin:
        return _member_organization_id(actor)
    if organization_guid is None:
        return None
    return get_active_organization_or_raise(session=session, guid=organization_guid).id


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
    organization_id = resolve_selectable_organization_id(
        session=session,
        actor=actor,
        organization_guid=organization_guid,
    )
    return [
        RoomAmenityOption.model_validate(room_amenity, from_attributes=True)
        for room_amenity in list_selectable_room_amenities(session=session, organization_id=organization_id)
    ]
