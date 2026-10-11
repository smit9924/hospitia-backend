from uuid import UUID

from sqlmodel import Session, col, func, or_, select

from booking.database.models.organization import Organization
from booking.database.models.organization_type import OrganizationType
from booking.schemas.organization_type_schemas import (
    OrganizationTypeListQueryParams,
    OrganizationTypeListResponse,
    OrganizationTypeResponse,
)

_SORT_COLUMNS = {
    "name": OrganizationType.name,
    "createdAt": OrganizationType.created_at,
    "updatedAt": OrganizationType.updated_at,
}


def get_organization_type_by_guid(*, session: Session, guid: UUID | str) -> OrganizationType | None:
    """Fetch an organization type by its public globally unique identifier.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    guid : UUID | str
        Organization type GUID to look up.

    Returns
    -------
    OrganizationType | None
        Matching organization type, or ``None`` if it does not exist.

    Raises
    ------
    SQLAlchemyError
        If the database query cannot be executed.
    """
    return session.exec(
        select(OrganizationType).where(OrganizationType.guid == guid)
    ).first()


def get_organization_type_by_name(*, session: Session, name: str) -> OrganizationType | None:
    """Fetch an organization type by its unique name.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    name : str
        Unique organization type name to look up.

    Returns
    -------
    OrganizationType | None
        Matching organization type, or ``None`` if it does not exist.

    Raises
    ------
    SQLAlchemyError
        If the database query cannot be executed.
    """
    return session.exec(
        select(OrganizationType).where(OrganizationType.name == name)
    ).first()


def create_organization_type(
    *,
    session: Session,
    name: str,
    description: str | None,
    actor_id: int | None,
) -> OrganizationType:
    """Create and commit an organization type.

    Parameters
    ----------
    session : Session
        Active database session used to persist the organization type.
    name : str
        Unique organization type name.
    description : str | None
        Optional organization type description.
    actor_id : int | None
        Internal ID of the user performing the operation, if available.

    Returns
    -------
    OrganizationType
        Newly created and refreshed organization type.

    Raises
    ------
    SQLAlchemyError
        If the organization type cannot be committed or refreshed.
    """
    organization_type = OrganizationType(
        name=name,
        description=description,
        # Pylance does not recognize inherited properties from AuditMixin.
        created_by=actor_id,  # type: ignore[call-arg]
        updated_by=actor_id,  # type: ignore[call-arg]
    )
    session.add(organization_type)
    session.commit()
    session.refresh(organization_type)
    return organization_type


def update_organization_type(
    *,
    session: Session,
    organization_type: OrganizationType,
    name: str,
    description: str | None,
    actor_id: int | None,
) -> OrganizationType:
    """Update and commit an organization type.

    Parameters
    ----------
    session : Session
        Active database session used to persist the update.
    organization_type : OrganizationType
        Organization type instance to update.
    name : str
        Replacement unique organization type name.
    description : str | None
        Replacement organization type description.
    actor_id : int | None
        Internal ID of the user performing the update, if available.

    Returns
    -------
    OrganizationType
        Updated and refreshed organization type.

    Raises
    ------
    SQLAlchemyError
        If the organization type cannot be committed or refreshed.
    """
    organization_type.name = name
    organization_type.description = description
    organization_type.updated_by = actor_id

    session.add(organization_type)
    session.commit()
    session.refresh(organization_type)
    return organization_type


def delete_organization_type(*, session: Session, organization_type: OrganizationType) -> None:
    """Delete an organization type from the database.

    Parameters
    ----------
    session : Session
        Active database session used to commit the deletion.
    organization_type : OrganizationType
        Organization type to delete.

    Returns
    -------
    None
        The deletion is committed successfully.

    Raises
    ------
    SQLAlchemyError
        If the deletion cannot be committed.
    """
    session.delete(organization_type)
    session.commit()


def has_active_organizations_of_type(*, session: Session, organization_type_id: int) -> bool:
    """Check whether an organization type is used by an active organization.

    Parameters
    ----------
    session : Session
        Active database session used to execute the count query.
    organization_type_id : int
        Internal ID of the organization type to check.

    Returns
    -------
    bool
        ``True`` when at least one active organization uses the type;
        otherwise ``False``.

    Raises
    ------
    SQLAlchemyError
        If the count query cannot be executed.
    """
    statement = (
        select(func.count())
        .select_from(Organization)
        .where(
            Organization.organization_type_id == organization_type_id,
            Organization.is_active == True,  # noqa: E712
        )
    )
    return session.exec(statement).one() > 0


def list_organization_types(
    *,
    session: Session,
    query: OrganizationTypeListQueryParams,
) -> OrganizationTypeListResponse:
    """List organization types with search, sorting, and pagination.

    Parameters
    ----------
    session : Session
        Active database session used to execute the queries.
    query : OrganizationTypeListQueryParams
        Search, sorting, and pagination options.

    Returns
    -------
    OrganizationTypeListResponse
        Paginated organization types and the total matching count.

    Raises
    ------
    KeyError
        If ``query.sort_by`` is not in the supported sort-column map.
    SQLAlchemyError
        If either database query cannot be executed.
    """
    statement = select(OrganizationType)
    count_statement = select(func.count()).select_from(OrganizationType)

    search_term = (query.search_term or "").strip()
    if search_term:
        pattern = f"%{search_term}%"
        search_filter = or_(col(OrganizationType.name).ilike(pattern))
        statement = statement.where(search_filter)
        count_statement = count_statement.where(search_filter)

    sort_column = _SORT_COLUMNS[query.sort_by]
    if query.sort_direction == "desc":
        statement = statement.order_by(col(sort_column).desc())
    else:
        statement = statement.order_by(col(sort_column).asc())

    offset = (query.page_number - 1) * query.page_size
    statement = statement.offset(offset).limit(query.page_size)

    total_count = session.exec(count_statement).one()
    organization_types = session.exec(statement).all()

    return OrganizationTypeListResponse(
        items=[
            OrganizationTypeResponse.model_validate(organization_type, from_attributes=True)
            for organization_type in organization_types
        ],
        total_count=total_count,
        page_number=query.page_number,
        page_size=query.page_size,
    )
