from sqlmodel import Session, select

from booking.database.models.organization_user_mapping import OrganizationUserMapping
from booking.database.models.users import UsersReplica
from booking.types.enums import OrganizationRole


def get_mapping(
    *,
    session: Session,
    organization_id: int,
    user_id: int,
    role: OrganizationRole,
) -> OrganizationUserMapping | None:
    """Find a user's organization mapping for a specific role.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    organization_id : int
        Internal ID of the organization.
    user_id : int
        Internal ID of the user.
    role : OrganizationRole
        Organization role required for the mapping.

    Returns
    -------
    OrganizationUserMapping | None
        Matching mapping, or ``None`` if no mapping exists.

    Raises
    ------
    SQLAlchemyError
        If the database query cannot be executed.
    """
    return session.exec(
        select(OrganizationUserMapping)
        .join(UsersReplica, UsersReplica.id == OrganizationUserMapping.user_id)
        .where(
            OrganizationUserMapping.organization_id == organization_id,
            OrganizationUserMapping.user_id == user_id,
            UsersReplica.role == role,
        )
    ).first()


def get_active_owner_mapping(*, session: Session, organization_id: int) -> OrganizationUserMapping | None:
    """Find the active owner mapping for an organization.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    organization_id : int
        Internal ID of the organization.

    Returns
    -------
    OrganizationUserMapping | None
        Active owner mapping, or ``None`` if no active owner exists.

    Raises
    ------
    SQLAlchemyError
        If the database query cannot be executed.
    """
    return session.exec(
        select(OrganizationUserMapping)
        .join(UsersReplica, UsersReplica.id == OrganizationUserMapping.user_id)
        .where(
            OrganizationUserMapping.organization_id == organization_id,
            UsersReplica.role == OrganizationRole.OWNER,
            OrganizationUserMapping.is_active == True,  # noqa: E712
        )
    ).first()


def get_or_create_mapping(
    *,
    session: Session,
    organization_id: int,
    user_id: int,
    role: OrganizationRole,
    actor_id: int | None,
) -> OrganizationUserMapping:
    """Return an existing mapping or create a new pending mapping.

    Parameters
    ----------
    session : Session
        Active database session used to query and add the mapping.
    organization_id : int
        Internal ID of the organization.
    user_id : int
        Internal ID of the user.
    role : OrganizationRole
        Role represented by the mapping.
    actor_id : int | None
        Internal ID of the user performing the operation, if available.

    Returns
    -------
    OrganizationUserMapping
        Existing mapping or newly added mapping.

    Raises
    ------
    SQLAlchemyError
        If the existing mapping cannot be queried.

    Notes
    -----
    A newly created mapping is added but not committed; the caller controls
    the transaction boundary.
    """
    mapping = get_mapping(session=session, organization_id=organization_id, user_id=user_id, role=role)
    if mapping is not None:
        return mapping

    mapping = OrganizationUserMapping(
        organization_id=organization_id,
        user_id=user_id,
        is_active=True,
        # Pylance does not recognize inherited properties from AuditMixin.
        created_by=actor_id,  # type: ignore[call-arg]
        updated_by=actor_id,  # type: ignore[call-arg]
    )
    session.add(mapping)
    return mapping


def is_user_active_owner_of_organization(*, session: Session, organization_id: int, user_id: int) -> bool:
    """Check whether a user is an active owner of an organization.

    Parameters
    ----------
    session : Session
        Active database session used to query the mapping.
    organization_id : int
        Internal ID of the organization.
    user_id : int
        Internal ID of the user.

    Returns
    -------
    bool
        ``True`` when the user has an active owner mapping; otherwise
        ``False``.

    Raises
    ------
    SQLAlchemyError
        If the mapping query cannot be executed.
    """
    mapping = get_mapping(session=session, organization_id=organization_id, user_id=user_id, role=OrganizationRole.OWNER)
    return mapping is not None and mapping.is_active


def is_user_active_manager_of_organization(*, session: Session, organization_id: int, user_id: int) -> bool:
    """Check whether a user is an active manager of an organization.

    Parameters
    ----------
    session : Session
        Active database session used to query the mapping.
    organization_id : int
        Internal ID of the organization.
    user_id : int
        Internal ID of the user.

    Returns
    -------
    bool
        ``True`` when the user has an active manager mapping; otherwise
        ``False``.

    Raises
    ------
    SQLAlchemyError
        If the mapping query cannot be executed.
    """
    mapping = get_mapping(session=session, organization_id=organization_id, user_id=user_id, role=OrganizationRole.MANAGER)
    return mapping is not None and mapping.is_active
