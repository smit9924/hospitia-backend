from uuid import UUID

from sqlalchemy.orm import aliased
from sqlmodel import Session, col, func, or_, select

from booking.database.models.address import Address
from booking.database.models.organization import Organization
from booking.database.models.organization_type import OrganizationType
from booking.database.models.organization_user_mapping import OrganizationUserMapping
from booking.database.models.users import UsersReplica
from booking.schemas.organization_schemas import (
    OrganizationListItem,
    OrganizationListQueryParams,
    OrganizationListResponse,
    OrganizationMembershipSummary,
)
from booking.types.enums import UserType

_SORT_COLUMNS = {
    "name": Organization.name,
    "createdAt": Organization.created_at,
    "updatedAt": Organization.updated_at,
}


def get_organization_by_guid(*, session: Session, guid: UUID | str) -> Organization | None:
    """Fetch an organization by its externally exposed globally unique ID.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    guid : UUID | str
        Organization GUID to look up.

    Returns
    -------
    Organization | None
        The matching organization, or ``None`` when no organization exists
        with the supplied GUID.

    Raises
    ------
    SQLAlchemyError
        If the database query cannot be executed.
    """
    return session.exec(
        select(Organization).where(Organization.guid == guid)
    ).first()


def create_organization(
    *,
    session: Session,
    name: str,
    description: str | None,
    organization_type_id: int,
    address_id: int,
    actor_id: int | None,
) -> Organization:
    """Create and flush a new active organization.

    Parameters
    ----------
    session : Session
        Active database session used to persist the organization.
    name : str
        Organization name.
    description : str | None
        Optional organization description.
    organization_type_id : int
        Internal ID of the organization's type.
    address_id : int
        Internal ID of the organization's address.
    actor_id : int | None
        Internal ID of the user performing the operation, if available.

    Returns
    -------
    Organization
        The newly created organization with pending changes flushed.

    Raises
    ------
    SQLAlchemyError
        If the organization cannot be added or flushed.

    Notes
    -----
    This function does not commit the transaction; the caller controls the
    transaction boundary.
    """
    # Pylance does not recognize inherited properties from AuditMixin
    # So, excluding from pylance call-arg checking
    organization = Organization(
        name=name,
        description=description,
        organization_type_id=organization_type_id,
        address_id=address_id,
        is_active=True,
        created_by=actor_id, # type: ignore[call-arg]
        updated_by=actor_id, # type: ignore[call-arg]
    )
    session.add(organization)
    session.flush()
    return organization


def update_organization(
    *,
    session: Session,
    organization: Organization,
    name: str,
    description: str | None,
    organization_type_id: int,
    is_active: bool,
    actor_id: int | None,
) -> Organization:
    """Update an organization's editable fields and flush the changes.

    Parameters
    ----------
    session : Session
        Active database session used to persist the update.
    organization : Organization
        Organization instance to update.
    name : str
        Replacement organization name.
    description : str | None
        Replacement organization description.
    organization_type_id : int
        Replacement internal organization type ID.
    is_active : bool
        Whether the organization remains active.
    actor_id : int | None
        Internal ID of the user performing the update, if available.

    Returns
    -------
    Organization
        The updated organization with pending changes flushed.

    Raises
    ------
    SQLAlchemyError
        If the organization cannot be added or flushed.

    Notes
    -----
    This function does not commit the transaction; the caller controls the
    transaction boundary.
    """
    organization.name = name
    organization.description = description
    organization.organization_type_id = organization_type_id
    organization.is_active = is_active
    organization.updated_by = actor_id

    session.add(organization)
    session.flush()
    return organization


def soft_delete_organization(*, session: Session, organization: Organization, actor_id: int | None) -> None:
    """Deactivate an organization while retaining its record and history.

    Parameters
    ----------
    session : Session
        Active database session used to persist the deletion state.
    organization : Organization
        Organization to deactivate.
    actor_id : int | None
        Internal ID of the user performing the deletion, if available.

    Returns
    -------
    None
        The organization is committed as inactive.

    Raises
    ------
    SQLAlchemyError
        If the organization cannot be committed.
    """
    organization.is_active = False
    organization.updated_by = actor_id
    session.add(organization)
    session.commit()


def _display_name(user: UsersReplica | None) -> str | None:
    """Build a display name from a user's name fields.

    Parameters
    ----------
    user : UsersReplica | None
        User whose display name should be generated.

    Returns
    -------
    str | None
        Trimmed first-and-last name, username fallback, or ``None`` when no
        user is supplied.
    """
    if user is None:
        return None
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    return full_name or user.username


def _build_organization_list_statement(
    query: OrganizationListQueryParams,
    *,
    organization_id_filter=None,
):
    """Build organization data and count queries.

    Parameters
    ----------
    query : OrganizationListQueryParams
        Search, sorting, and pagination options.
    organization_id_filter : SQL expression | None
        Optional additional filter restricting organizations by ID.

    Returns
    -------
    tuple
        A tuple containing the organization select statement and its matching
        total-count statement.

    Raises
    ------
    KeyError
        If ``query.sort_by`` is not present in the supported sort-column map.
    SQLAlchemyError
        If SQLAlchemy cannot construct the query expressions.
    """
    owner_mapping = aliased(OrganizationUserMapping)
    owner_alias = aliased(UsersReplica)
    created_by_alias = aliased(UsersReplica)
    updated_by_alias = aliased(UsersReplica)
    owner_user_ids = select(UsersReplica.id).where(UsersReplica.role == UserType.OWNER)

    statement = (
        select(Organization, OrganizationType, Address, owner_alias, created_by_alias, updated_by_alias) # type: ignore
        .join(OrganizationType, Organization.organization_type_id == OrganizationType.id)
        .join(Address, Organization.address_id == Address.id)
        # Join only the active OWNER mapping: joining every active mapping
        # (managers included) would repeat the organization once per member.
        .outerjoin(
            owner_mapping,
            (owner_mapping.organization_id == Organization.id)
            & (owner_mapping.is_active == True)  # noqa: E712
            & col(owner_mapping.user_id).in_(owner_user_ids),
        )
        .outerjoin(owner_alias, owner_alias.id == owner_mapping.user_id)
        .outerjoin(created_by_alias, created_by_alias.id == Organization.created_by)
        .outerjoin(updated_by_alias, updated_by_alias.id == Organization.updated_by)
        .where(Organization.is_active == True)  # noqa: E712
    )

    count_statement = select(func.count()).select_from(Organization).where(Organization.is_active == True)  # noqa: E712

    if organization_id_filter is not None:
        statement = statement.where(organization_id_filter)
        count_statement = count_statement.where(organization_id_filter)

    search_term = (query.search_term or "").strip()
    if search_term:
        pattern = f"%{search_term}%"
        search_filter = or_(col(Organization.name).ilike(pattern))
        statement = statement.where(search_filter)
        count_statement = count_statement.where(search_filter)

    sort_column = _SORT_COLUMNS[query.sort_by]
    if query.sort_direction == "desc":
        statement = statement.order_by(col(sort_column).desc())
    else:
        statement = statement.order_by(col(sort_column).asc())

    offset = (query.page_number - 1) * query.page_size
    statement = statement.offset(offset).limit(query.page_size)

    return statement, count_statement


def _run_organization_list_query(
    *,
    session: Session,
    query: OrganizationListQueryParams,
    organization_id_filter=None,
) -> OrganizationListResponse:
    """Execute organization queries and map rows into response items.

    Parameters
    ----------
    session : Session
        Active database session used to execute both statements.
    query : OrganizationListQueryParams
        Search, sorting, and pagination options.
    organization_id_filter : SQL expression | None
        Optional additional filter restricting organizations by ID.

    Returns
    -------
    OrganizationListResponse
        Paginated organizations and the total number of matching records.

    Raises
    ------
    KeyError
        If ``query.sort_by`` is not present in the supported sort-column map.
    SQLAlchemyError
        If either database query cannot be executed.
    """
    statement, count_statement = _build_organization_list_statement(
        query, organization_id_filter=organization_id_filter
    )

    total_count = session.exec(count_statement).one()
    rows = session.exec(statement).all()

    items = [
        OrganizationListItem(
            guid=organization.guid,
            name=organization.name,
            organization_type_name=organization_type.name,
            owner_display_name=_display_name(owner),
            address_line_1=address.address_line_1,
            city=address.city,
            state=address.state,
            country=address.country,
            is_active=organization.is_active,
            created_by_display_name=_display_name(created_by),
            created_at=organization.created_at,
            updated_by_display_name=_display_name(updated_by),
            updated_at=organization.updated_at,
        )
        for organization, organization_type, address, owner, created_by, updated_by in rows
    ]

    return OrganizationListResponse(
        items=items,
        total_count=total_count,
        page_number=query.page_number,
        page_size=query.page_size,
    )


def list_organizations_for_admin(*, session: Session, query: OrganizationListQueryParams) -> OrganizationListResponse:
    """List all active organizations for an administrator.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    query : OrganizationListQueryParams
        Search, sorting, and pagination options.

    Returns
    -------
    OrganizationListResponse
        Paginated active organizations and the total matching count.

    Raises
    ------
    KeyError
        If ``query.sort_by`` is not supported.
    SQLAlchemyError
        If the database query cannot be executed.
    """
    return _run_organization_list_query(session=session, query=query)


def list_organizations_for_owner(
    *, session: Session, owner_user_id: int, query: OrganizationListQueryParams
) -> OrganizationListResponse:
    """List active organizations owned by a specific user.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    owner_user_id : int
        Internal ID of the user whose active owner mappings are used.
    query : OrganizationListQueryParams
        Search, sorting, and pagination options.

    Returns
    -------
    OrganizationListResponse
        Paginated active organizations mapped to the user as an owner.

    Raises
    ------
    KeyError
        If ``query.sort_by`` is not supported.
    SQLAlchemyError
        If the database query cannot be executed.
    """
    owned_organization_ids = (
        select(OrganizationUserMapping.organization_id)
        .join(UsersReplica, UsersReplica.id == OrganizationUserMapping.user_id) # pyright: ignore[reportArgumentType]
        .where(
            OrganizationUserMapping.user_id == owner_user_id,
            UsersReplica.role == UserType.OWNER,
            OrganizationUserMapping.is_active == True,  # noqa: E712
        )
    )
    return _run_organization_list_query(
        session=session,
        query=query,
        organization_id_filter=Organization.id.in_(owned_organization_ids), # type: ignore
    )


def list_organizations_for_manager(
    *, session: Session, manager_user_id: int, query: OrganizationListQueryParams
) -> OrganizationListResponse:
    """List active organizations managed by a specific user.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    manager_user_id : int
        Internal ID of the user whose active manager mappings are used.
    query : OrganizationListQueryParams
        Search, sorting, and pagination options.

    Returns
    -------
    OrganizationListResponse
        Paginated active organizations mapped to the user as a manager.

    Raises
    ------
    KeyError
        If ``query.sort_by`` is not supported.
    SQLAlchemyError
        If the database query cannot be executed.
    """
    managed_organization_ids = (
        select(OrganizationUserMapping.organization_id)
        .join(UsersReplica, UsersReplica.id == OrganizationUserMapping.user_id) # pyright: ignore[reportArgumentType]
        .where(
            OrganizationUserMapping.user_id == manager_user_id,
            UsersReplica.role == UserType.MANAGER,
            OrganizationUserMapping.is_active == True,  # noqa: E712
        )
    )
    return _run_organization_list_query(
        session=session,
        query=query,
        organization_id_filter=Organization.id.in_(managed_organization_ids), # type: ignore
    )


def _to_membership_summary(
    organization: Organization,
    organization_type: OrganizationType,
    address: Address,
) -> OrganizationMembershipSummary:
    """Map an organization row and its type/address into a membership summary."""
    return OrganizationMembershipSummary(
        guid=organization.guid,
        name=organization.name,
        organization_type_name=organization_type.name,
        city=address.city,
    )


def list_active_member_organizations(*, session: Session, user_id: int) -> list[OrganizationMembershipSummary]:
    """List active organizations a user is actively mapped to, by name.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    user_id : int
        Internal ID of the user whose active mappings are used.

    Returns
    -------
    list[OrganizationMembershipSummary]
        Organizations where both the organization and the user's mapping
        are active, sorted by name ascending. Empty when there are none.

    Raises
    ------
    SQLAlchemyError
        If the database query cannot be executed.
    """
    rows = session.exec(
        select(Organization, OrganizationType, Address)  # type: ignore
        .join(OrganizationUserMapping, OrganizationUserMapping.organization_id == Organization.id)
        .join(OrganizationType, Organization.organization_type_id == OrganizationType.id)
        .join(Address, Organization.address_id == Address.id)
        .where(
            OrganizationUserMapping.user_id == user_id,
            OrganizationUserMapping.is_active == True,  # noqa: E712
            Organization.is_active == True,  # noqa: E712
        )
        .order_by(col(Organization.name).asc())
    ).all()
    return [_to_membership_summary(*row) for row in rows]


def get_active_member_organization(
    *, session: Session, user_id: int, organization_guid: UUID
) -> Organization | None:
    """Fetch an active organization only if the user is actively mapped to it.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    user_id : int
        Internal ID of the user whose mapping must be active.
    organization_guid : UUID
        Organization GUID to look up.

    Returns
    -------
    Organization | None
        The organization, or ``None`` when it does not exist, is inactive,
        or the user has no active mapping to it.

    Raises
    ------
    SQLAlchemyError
        If the database query cannot be executed.
    """
    return session.exec(
        select(Organization)
        .join(OrganizationUserMapping, OrganizationUserMapping.organization_id == Organization.id)  # pyright: ignore[reportArgumentType]
        .where(
            Organization.guid == organization_guid,
            Organization.is_active == True,  # noqa: E712
            OrganizationUserMapping.user_id == user_id,
            OrganizationUserMapping.is_active == True,  # noqa: E712
        )
    ).first()


def get_organization_membership_summary(
    *, session: Session, organization_id: int
) -> OrganizationMembershipSummary | None:
    """Build the membership summary of a single organization.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    organization_id : int
        Internal ID of the organization.

    Returns
    -------
    OrganizationMembershipSummary | None
        Summary of the organization, or ``None`` if it does not exist.

    Raises
    ------
    SQLAlchemyError
        If the database query cannot be executed.
    """
    row = session.exec(
        select(Organization, OrganizationType, Address)  # type: ignore
        .join(OrganizationType, Organization.organization_type_id == OrganizationType.id)
        .join(Address, Organization.address_id == Address.id)
        .where(Organization.id == organization_id)
    ).first()
    return _to_membership_summary(*row) if row is not None else None
