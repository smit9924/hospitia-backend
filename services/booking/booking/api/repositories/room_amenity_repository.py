from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import ColumnElement
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, func, or_, select

from booking.api.repositories.list_query_helpers import (
    apply_sorting_and_pagination,
    build_contains_pattern,
)
from booking.database.models.organization import Organization
from booking.database.models.room_amenity import RoomAmenity
from booking.schemas.room_amenity_schemas import (
    RoomAmenityListQueryParams,
    RoomAmenityListResponse,
    RoomAmenityResponse,
)

_SORT_COLUMNS = {
    "name": RoomAmenity.name,
    "createdAt": RoomAmenity.created_at,
    "updatedAt": RoomAmenity.updated_at,
}

_IS_ACTIVE = RoomAmenity.is_active == True  # noqa: E712
_IS_DEFAULT = col(RoomAmenity.organization_id).is_(None)


def _visible_to_organization(organization_id: int | None) -> ColumnElement[bool]:
    """Filter for the amenities an organization may use: the defaults plus its own custom ones.

    Parameters
    ----------
    organization_id : int | None
        Internal ID of the organization, or ``None`` to match defaults only.
    """
    if organization_id is None:
        return _IS_DEFAULT
    return or_(_IS_DEFAULT, RoomAmenity.organization_id == organization_id)


def get_active_room_amenity_by_guid(*, session: Session, guid: UUID | str) -> RoomAmenity | None:
    """Fetch an active room amenity, with its owning organization, by GUID.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    guid : UUID | str
        Room amenity GUID to look up.

    Returns
    -------
    RoomAmenity | None
        Matching active amenity, or ``None`` if it does not exist or was
        deleted.
    """
    return session.exec(
        select(RoomAmenity)
        .options(selectinload(RoomAmenity.organization))  # type: ignore[arg-type]
        .where(RoomAmenity.guid == guid, _IS_ACTIVE)
    ).first()


def get_active_room_amenities_by_guids(*, session: Session, guids: Sequence[UUID]) -> list[RoomAmenity]:
    """Fetch the active room amenities matching any of the given GUIDs.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    guids : Sequence[UUID]
        Room amenity GUIDs to look up.

    Returns
    -------
    list[RoomAmenity]
        The active amenities found; missing or deleted GUIDs are skipped.
    """
    if not guids:
        return []
    return list(session.exec(select(RoomAmenity).where(col(RoomAmenity.guid).in_(guids), _IS_ACTIVE)).all())


def find_active_room_amenity_by_name(
    *,
    session: Session,
    name: str,
    organization_id: int | None,
) -> RoomAmenity | None:
    """Find an active amenity with the same name, ignoring case, in one scope.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    name : str
        Amenity name to look for.
    organization_id : int | None
        Organization whose custom amenities are searched, or ``None`` to
        search the default amenities.

    Returns
    -------
    RoomAmenity | None
        The amenity using that name in that scope, or ``None``.
    """
    scope_filter = _IS_DEFAULT if organization_id is None else RoomAmenity.organization_id == organization_id
    return session.exec(
        select(RoomAmenity).where(
            func.lower(RoomAmenity.name) == name.lower(),
            scope_filter,
            _IS_ACTIVE,
        )
    ).first()


def create_room_amenity(
    *,
    session: Session,
    name: str,
    description: str | None,
    organization_id: int | None,
    actor_id: int | None,
) -> RoomAmenity:
    """Create and commit a room amenity.

    Parameters
    ----------
    session : Session
        Active database session used to persist the amenity.
    name : str
        Amenity name.
    description : str | None
        Optional amenity description.
    organization_id : int | None
        Owning organization of a custom amenity, or ``None`` for a default.
    actor_id : int | None
        Internal ID of the user performing the operation, if available.

    Returns
    -------
    RoomAmenity
        Newly created amenity with its organization loaded.
    """
    room_amenity = RoomAmenity(
        name=name,
        description=description,
        organization_id=organization_id,
        # Pylance does not recognize inherited properties from AuditMixin.
        created_by=actor_id,  # type: ignore[call-arg]
        updated_by=actor_id,  # type: ignore[call-arg]
    )
    session.add(room_amenity)
    session.commit()
    session.refresh(room_amenity)
    return room_amenity


def update_room_amenity(
    *,
    session: Session,
    room_amenity: RoomAmenity,
    name: str,
    description: str | None,
    actor_id: int | None,
) -> RoomAmenity:
    """Update and commit a room amenity's name and description.

    The amenity's scope (default or owning organization) never changes.

    Parameters
    ----------
    session : Session
        Active database session used to persist the update.
    room_amenity : RoomAmenity
        Amenity instance to update.
    name : str
        Replacement amenity name.
    description : str | None
        Replacement amenity description.
    actor_id : int | None
        Internal ID of the user performing the update, if available.

    Returns
    -------
    RoomAmenity
        Updated and refreshed amenity.
    """
    room_amenity.name = name
    room_amenity.description = description
    room_amenity.updated_by = actor_id

    session.add(room_amenity)
    session.commit()
    session.refresh(room_amenity)
    return room_amenity


def soft_delete_room_amenity(*, session: Session, room_amenity: RoomAmenity, actor_id: int | None) -> None:
    """Soft-delete a room amenity by marking it inactive.

    Parameters
    ----------
    session : Session
        Active database session used to commit the change.
    room_amenity : RoomAmenity
        Amenity to deactivate.
    actor_id : int | None
        Internal ID of the user performing the deletion, if available.
    """
    room_amenity.is_active = False
    room_amenity.updated_by = actor_id
    session.add(room_amenity)
    session.commit()


def list_selectable_room_amenities(*, session: Session, organization_id: int | None) -> list[RoomAmenity]:
    """List the active amenities an organization may assign, ordered by name.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    organization_id : int | None
        Organization whose custom amenities are included next to the
        defaults, or ``None`` for the defaults only.

    Returns
    -------
    list[RoomAmenity]
        Default and custom amenities ordered by name, case-insensitively.
    """
    return list(
        session.exec(
            select(RoomAmenity)
            .where(_IS_ACTIVE, _visible_to_organization(organization_id))
            .order_by(func.lower(RoomAmenity.name))
        ).all()
    )


def _list_room_amenities_page(
    *,
    session: Session,
    query: RoomAmenityListQueryParams,
    visibility_filter: ColumnElement[bool],
) -> RoomAmenityListResponse:
    """List active amenities matching `visibility_filter` with search, sorting and pagination."""
    statement = (
        select(RoomAmenity)
        .options(selectinload(RoomAmenity.organization))  # type: ignore[arg-type]
        .where(_IS_ACTIVE, visibility_filter)
    )
    count_statement = select(func.count()).select_from(RoomAmenity).where(_IS_ACTIVE, visibility_filter)

    search_pattern = build_contains_pattern(query.search_term)
    if search_pattern:
        search_filter = col(RoomAmenity.name).ilike(search_pattern)
        statement = statement.where(search_filter)
        count_statement = count_statement.where(search_filter)

    statement = apply_sorting_and_pagination(
        statement=statement,
        sort_column=_SORT_COLUMNS[query.sort_by],
        sort_direction=query.sort_direction,
        page_number=query.page_number,
        page_size=query.page_size,
    )

    total_count = session.exec(count_statement).one()
    room_amenities = session.exec(statement).all()

    return RoomAmenityListResponse(
        items=[RoomAmenityResponse.model_validate(room_amenity, from_attributes=True) for room_amenity in room_amenities],
        total_count=total_count,
        page_number=query.page_number,
        page_size=query.page_size,
    )


def list_room_amenities_for_admin(*, session: Session, query: RoomAmenityListQueryParams) -> RoomAmenityListResponse:
    """List every default amenity plus the custom amenities of active organizations.

    Parameters
    ----------
    session : Session
        Active database session used to execute the queries.
    query : RoomAmenityListQueryParams
        Search, sorting, and pagination options.

    Returns
    -------
    RoomAmenityListResponse
        Paginated amenities and the total matching count.
    """
    active_organization_ids = select(Organization.id).where(Organization.is_active == True)  # noqa: E712
    visibility_filter = or_(_IS_DEFAULT, col(RoomAmenity.organization_id).in_(active_organization_ids))
    return _list_room_amenities_page(session=session, query=query, visibility_filter=visibility_filter)


def list_room_amenities_for_organization(
    *,
    session: Session,
    query: RoomAmenityListQueryParams,
    organization_id: int,
) -> RoomAmenityListResponse:
    """List the default amenities plus the custom amenities of one organization.

    Parameters
    ----------
    session : Session
        Active database session used to execute the queries.
    query : RoomAmenityListQueryParams
        Search, sorting, and pagination options.
    organization_id : int
        Internal ID of the organization.

    Returns
    -------
    RoomAmenityListResponse
        Paginated amenities and the total matching count.
    """
    return _list_room_amenities_page(
        session=session,
        query=query,
        visibility_filter=_visible_to_organization(organization_id),
    )
