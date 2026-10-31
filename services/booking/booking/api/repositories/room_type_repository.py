from collections import defaultdict
from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from sqlalchemy import ColumnElement
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, delete, func, select

from booking.api.repositories.list_query_helpers import (
    apply_sorting_and_pagination,
    build_contains_pattern,
)
from booking.database.models.organization import Organization
from booking.database.models.room_amenity import RoomAmenity
from booking.database.models.room_type import RoomType
from booking.database.models.room_type_amenity_mapping import RoomTypeAmenityMapping
from booking.schemas.room_type_schemas import RoomTypeListQueryParams

_SORT_COLUMNS = {
    "name": RoomType.name,
    "capacity": RoomType.capacity,
    "costPerNight": RoomType.cost_per_night,
    "createdAt": RoomType.created_at,
    "updatedAt": RoomType.updated_at,
}

_IS_ACTIVE = RoomType.is_active == True  # noqa: E712


def get_active_room_type_by_guid(*, session: Session, guid: UUID | str) -> RoomType | None:
    """Fetch an active room type, with its organization and currency, by GUID.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    guid : UUID | str
        Room type GUID to look up.

    Returns
    -------
    RoomType | None
        Matching active room type, or ``None`` if it does not exist or was
        deleted.
    """
    return session.exec(
        select(RoomType)
        .options(selectinload(RoomType.organization), selectinload(RoomType.currency_unit))  # type: ignore[arg-type]
        .where(RoomType.guid == guid, _IS_ACTIVE)
    ).first()


def find_active_room_type_by_name(*, session: Session, organization_id: int, name: str) -> RoomType | None:
    """Find an active room type of the organization with the same name, ignoring case.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    organization_id : int
        Internal ID of the organization.
    name : str
        Room type name to look for.

    Returns
    -------
    RoomType | None
        The room type using that name, or ``None``.
    """
    return session.exec(
        select(RoomType).where(
            RoomType.organization_id == organization_id,
            func.lower(RoomType.name) == name.lower(),
            _IS_ACTIVE,
        )
    ).first()


def _replace_room_type_amenities(
    *,
    session: Session,
    room_type_id: int,
    room_amenity_ids: Sequence[int],
    actor_id: int | None,
) -> None:
    """Make the room type's amenity mappings match `room_amenity_ids` (not committed).

    Mappings that are no longer selected are removed; new ones are added;
    unchanged ones keep their original audit data.
    """
    existing_amenity_ids = set(
        session.exec(
            select(RoomTypeAmenityMapping.room_amenity_id).where(RoomTypeAmenityMapping.room_type_id == room_type_id)
        ).all()
    )
    selected_amenity_ids = set(room_amenity_ids)

    removed_amenity_ids = existing_amenity_ids - selected_amenity_ids
    if removed_amenity_ids:
        session.exec(  # type: ignore[call-overload]
            delete(RoomTypeAmenityMapping).where(
                col(RoomTypeAmenityMapping.room_type_id) == room_type_id,
                col(RoomTypeAmenityMapping.room_amenity_id).in_(removed_amenity_ids),
            )
        )

    for room_amenity_id in selected_amenity_ids - existing_amenity_ids:
        session.add(
            RoomTypeAmenityMapping(
                room_type_id=room_type_id,
                room_amenity_id=room_amenity_id,
                # Pylance does not recognize inherited properties from AuditMixin.
                created_by=actor_id,  # type: ignore[call-arg]
                updated_by=actor_id,  # type: ignore[call-arg]
            )
        )


def create_room_type(
    *,
    session: Session,
    organization_id: int,
    name: str,
    description: str | None,
    capacity: int,
    cost_per_night: Decimal,
    currency_unit_id: int,
    room_amenity_ids: Sequence[int],
    actor_id: int | None,
) -> RoomType:
    """Create a room type with its amenity mappings in one transaction.

    Parameters
    ----------
    session : Session
        Active database session used to persist the room type.
    organization_id : int
        Internal ID of the owning organization.
    name, description, capacity, cost_per_night
        Room type fields, see `RoomType`.
    currency_unit_id : int
        Internal ID of the currency of `cost_per_night`.
    room_amenity_ids : Sequence[int]
        Internal IDs of the room type's amenities.
    actor_id : int | None
        Internal ID of the user performing the operation, if available.

    Returns
    -------
    RoomType
        Newly created and refreshed room type.
    """
    room_type = RoomType(
        organization_id=organization_id,
        name=name,
        description=description,
        capacity=capacity,
        cost_per_night=cost_per_night,
        currency_unit_id=currency_unit_id,
        # Pylance does not recognize inherited properties from AuditMixin.
        created_by=actor_id,  # type: ignore[call-arg]
        updated_by=actor_id,  # type: ignore[call-arg]
    )
    session.add(room_type)
    session.flush()  # Assigns room_type.id for the mappings.
    _replace_room_type_amenities(
        session=session,
        room_type_id=room_type.id,  # type: ignore[arg-type]
        room_amenity_ids=room_amenity_ids,
        actor_id=actor_id,
    )
    session.commit()
    session.refresh(room_type)
    return room_type


def update_room_type(
    *,
    session: Session,
    room_type: RoomType,
    name: str,
    description: str | None,
    capacity: int,
    cost_per_night: Decimal,
    currency_unit_id: int,
    room_amenity_ids: Sequence[int],
    actor_id: int | None,
) -> RoomType:
    """Update a room type and replace its amenities in one transaction.

    The owning organization never changes.

    Parameters
    ----------
    session : Session
        Active database session used to persist the update.
    room_type : RoomType
        Room type instance to update.
    name, description, capacity, cost_per_night, currency_unit_id, room_amenity_ids
        Replacement values, see `create_room_type`.
    actor_id : int | None
        Internal ID of the user performing the update, if available.

    Returns
    -------
    RoomType
        Updated and refreshed room type.
    """
    room_type.name = name
    room_type.description = description
    room_type.capacity = capacity
    room_type.cost_per_night = cost_per_night
    room_type.currency_unit_id = currency_unit_id
    room_type.updated_by = actor_id
    session.add(room_type)
    _replace_room_type_amenities(
        session=session,
        room_type_id=room_type.id,  # type: ignore[arg-type]
        room_amenity_ids=room_amenity_ids,
        actor_id=actor_id,
    )
    session.commit()
    session.refresh(room_type)
    return room_type


def soft_delete_room_type(*, session: Session, room_type: RoomType, actor_id: int | None) -> None:
    """Soft-delete a room type by marking it inactive; its amenity mappings are kept as history.

    Parameters
    ----------
    session : Session
        Active database session used to commit the change.
    room_type : RoomType
        Room type to deactivate.
    actor_id : int | None
        Internal ID of the user performing the deletion, if available.
    """
    room_type.is_active = False
    room_type.updated_by = actor_id
    session.add(room_type)
    session.commit()


def get_active_amenities_by_room_type_id(
    *,
    session: Session,
    room_type_ids: Sequence[int],
) -> dict[int, list[RoomAmenity]]:
    """Load the active amenities of several room types in one query.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    room_type_ids : Sequence[int]
        Internal IDs of the room types.

    Returns
    -------
    dict[int, list[RoomAmenity]]
        Amenities per room type ID, ordered by name (case-insensitively);
        room types without amenities are absent.
    """
    if not room_type_ids:
        return {}
    rows = session.exec(
        select(RoomTypeAmenityMapping.room_type_id, RoomAmenity)
        .join(RoomAmenity, RoomAmenity.id == RoomTypeAmenityMapping.room_amenity_id)  # type: ignore[arg-type]
        .where(
            col(RoomTypeAmenityMapping.room_type_id).in_(room_type_ids),
            RoomAmenity.is_active == True,  # noqa: E712
        )
        .order_by(func.lower(RoomAmenity.name))
    ).all()

    amenities_by_room_type_id: dict[int, list[RoomAmenity]] = defaultdict(list)
    for room_type_id, room_amenity in rows:
        amenities_by_room_type_id[room_type_id].append(room_amenity)
    return amenities_by_room_type_id


def list_room_types_page(
    *,
    session: Session,
    query: RoomTypeListQueryParams,
    organization_id: int | None,
) -> tuple[list[RoomType], int]:
    """List active room types with search, sorting, and pagination.

    Parameters
    ----------
    session : Session
        Active database session used to execute the queries.
    query : RoomTypeListQueryParams
        Search, sorting, and pagination options.
    organization_id : int | None
        Restricts the list to one organization; ``None`` lists the room
        types of every active organization (admin view).

    Returns
    -------
    tuple[list[RoomType], int]
        The page of room types (organization and currency loaded) and the
        total matching count.
    """
    filters: list[ColumnElement[bool]] = [_IS_ACTIVE]
    if organization_id is None:
        active_organization_ids = select(Organization.id).where(Organization.is_active == True)  # noqa: E712
        filters.append(col(RoomType.organization_id).in_(active_organization_ids))
    else:
        filters.append(RoomType.organization_id == organization_id)

    search_pattern = build_contains_pattern(query.search_term)
    if search_pattern:
        filters.append(col(RoomType.name).ilike(search_pattern))

    statement = (
        select(RoomType)
        .options(selectinload(RoomType.organization), selectinload(RoomType.currency_unit))  # type: ignore[arg-type]
        .where(*filters)
    )
    statement = apply_sorting_and_pagination(
        statement=statement,
        sort_column=_SORT_COLUMNS[query.sort_by],
        sort_direction=query.sort_direction,
        page_number=query.page_number,
        page_size=query.page_size,
    )
    count_statement = select(func.count()).select_from(RoomType).where(*filters)

    return list(session.exec(statement).all()), session.exec(count_statement).one()


def has_active_room_types_using_currency_unit(*, session: Session, currency_unit_id: int) -> bool:
    """Check whether an active room type prices in the currency unit."""
    statement = select(func.count()).select_from(RoomType).where(RoomType.currency_unit_id == currency_unit_id, _IS_ACTIVE)
    return session.exec(statement).one() > 0


def has_active_room_types_using_amenity(*, session: Session, room_amenity_id: int) -> bool:
    """Check whether an active room type lists the amenity."""
    statement = (
        select(func.count())
        .select_from(RoomTypeAmenityMapping)
        .join(RoomType, RoomType.id == RoomTypeAmenityMapping.room_type_id)  # type: ignore[arg-type]
        .where(RoomTypeAmenityMapping.room_amenity_id == room_amenity_id, _IS_ACTIVE)
    )
    return session.exec(statement).one() > 0


def has_active_room_types_in_organization(*, session: Session, organization_id: int) -> bool:
    """Check whether the organization still has an active room type."""
    statement = select(func.count()).select_from(RoomType).where(RoomType.organization_id == organization_id, _IS_ACTIVE)
    return session.exec(statement).one() > 0
