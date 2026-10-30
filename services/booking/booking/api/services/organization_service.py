import logging
from uuid import UUID

from sqlmodel import Session

from booking.api.repositories.organization_repository import (
    create_organization,
    get_active_member_organization,
    get_organization_by_guid,
    get_organization_membership_summary,
    list_active_member_organizations,
    list_organizations_for_admin,
    list_organizations_for_manager,
    list_organizations_for_owner,
    soft_delete_organization,
)
from booking.api.repositories.organization_repository import (
    update_organization as update_organization_repo,
)
from booking.api.repositories.organization_type_repository import (
    get_organization_type_by_guid,
)
from booking.api.repositories.organization_user_mapping_repository import (
    get_active_owner_mapping,
    is_user_active_manager_of_organization,
    is_user_active_owner_of_organization,
)
from booking.api.repositories.user_repository import (
    get_user_replica_by_guid,
    get_user_replica_by_id,
)
from booking.database.models.address import Address
from booking.database.models.organization import Organization
from booking.database.models.organization_user_mapping import OrganizationUserMapping
from booking.database.models.users import UsersReplica
from booking.exceptions.definitions.not_found_exceptions import (
    AddressNotFoundException,
    OrganizationNotFoundException,
    OrganizationTypeNotFoundException,
    UserNotFoundException,
)
from booking.exceptions.definitions.security_exceptions import (
    ActiveOrganizationInvalidException,
    OrganizationAccessForbiddenException,
)
from booking.exceptions.definitions.validation_exceptions import (
    UserRoleMismatchForOrganizationException,
)
from booking.schemas.organization_schemas import (
    ActiveOrganization,
    AddressInput,
    AddressResponse,
    OrganizationCreateAdminRequest,
    OrganizationCreateOwnerRequest,
    OrganizationListQueryParams,
    OrganizationListResponse,
    OrganizationMembershipListResponse,
    OrganizationMembershipSummary,
    OrganizationMemberSummary,
    OrganizationResponse,
)
from booking.schemas.organization_type_schemas import OrganizationTypeResponse
from booking.types.enums import UserType

log = logging.getLogger(__name__)


def get_user_id_from_user_guid(*, session: Session, guid: str) -> int:
    """Resolve a user GUID to its internal user ID.

    Parameters
    ----------
    session : Session
        Active database session used to query the user replica.
    guid : str
        External user GUID to resolve.

    Returns
    -------
    int
        Internal ID of the resolved user.

    Raises
    ------
    UserNotFoundException
        If no user exists for the supplied GUID or the user has no ID.
    """
    actor = get_user_replica_by_guid(session=session, guid=guid)
    if actor is None or actor.id is None:
        raise UserNotFoundException()
    return actor.id


def create_organization_with_owner(
    *,
    session: Session,
    name: str,
    description: str | None,
    organization_type_id: int,
    address_input: AddressInput,
    owner_user_id: int,
    actor_user_id: int,
) -> Organization:
    """
    Create an organization, its address, and the initial active OWNER
    mapping, all within a single transaction. An organization is never
    persisted without its address and owner mapping.

    Parameters
    ----------
    session : Session
        Active database session used to persist the organization.
    name : str
        Organization name.
    description : str | None
        Optional organization description.
    organization_type_id : int
        Internal ID of the organization type.
    address_input : AddressInput
        Address data for the organization.
    owner_user_id : int
        Internal ID of the initial owner.
    actor_user_id : int
        Internal ID of the user performing the operation.

    Returns
    -------
    Organization
        The newly created organization after the transaction is committed.

    Raises
    ------
    SQLAlchemyError
        If the database transaction cannot be flushed, committed, or refreshed.
    """
    address = Address(
        **address_input.model_dump(),
        created_by=actor_user_id, # type: ignore[call-arg]
        updated_by=actor_user_id, # type: ignore[call-arg]
    )
    session.add(address)
    session.flush()  # assigns address.id without committing
    if address.id is None:
        raise AddressNotFoundException()

    organization = create_organization(
        session=session,
        name=name,
        description=description,
        organization_type_id=organization_type_id,
        address_id=address.id,
        actor_id=actor_user_id,
    )
    if organization.id is None:
        raise OrganizationNotFoundException()

    mapping = OrganizationUserMapping(
        organization_id=organization.id,
        user_id=owner_user_id,
        is_active=True,
        created_by=actor_user_id, # type: ignore[call-arg]
        updated_by=actor_user_id, # type: ignore[call-arg]
    )
    session.add(mapping)

    session.commit()  # organization + address + owner mapping succeed or fail together
    session.refresh(organization)
    return organization


def _update_organization_address(
    *,
    session: Session,
    organization: Organization,
    address_input: AddressInput,
    actor_user_id: int,
) -> None:
    """Update the address belonging to an organization.

    Parameters
    ----------
    session : Session
        Active database session used to persist the address.
    organization : Organization
        Organization whose address should be updated.
    address_input : AddressInput
        Replacement address data.
    actor_user_id : int
        Internal ID of the user performing the update.

    Returns
    -------
    None
        The updated address is added to the current transaction.

    Raises
    ------
    AddressNotFoundException
        If the organization does not reference an existing address.
    SQLAlchemyError
        If the database session cannot retrieve or add the address.
    """
    address = session.get(Address, organization.address_id)
    # An organization must always reference an address; fail explicitly if data is inconsistent.
    if address is None:
        raise AddressNotFoundException()
    address.address_line_1 = address_input.address_line_1
    address.address_line_2 = address_input.address_line_2
    address.landmark = address_input.landmark
    address.city = address_input.city
    address.state = address_input.state
    address.country = address_input.country
    address.postal_code = address_input.postal_code
    address.updated_by = actor_user_id
    session.add(address)


def _update_organization_full(
    *,
    session: Session,
    organization: Organization,
    name: str,
    description: str | None,
    organization_type_id: int,
    address_input: AddressInput,
    is_active: bool,
    actor_user_id: int,
) -> Organization:
    """Update an organization and its address in one transaction.

    Parameters
    ----------
    session : Session
        Active database session used to persist the changes.
    organization : Organization
        Organization to update.
    name : str
        New organization name.
    description : str | None
        Optional replacement organization description.
    organization_type_id : int
        Internal ID of the replacement organization type.
    address_input : AddressInput
        Replacement address data.
    is_active : bool
        Whether the organization should remain active.
    actor_user_id : int
        Internal ID of the user performing the update.

    Returns
    -------
    Organization
        The updated organization after the transaction is committed.

    Raises
    ------
    AddressNotFoundException
        If the organization does not reference an existing address.
    SQLAlchemyError
        If the database transaction cannot be committed or refreshed.
    """
    _update_organization_address(
        session=session, organization=organization, address_input=address_input, actor_user_id=actor_user_id
    )
    organization = update_organization_repo(
        session=session,
        organization=organization,
        name=name,
        description=description,
        organization_type_id=organization_type_id,
        is_active=is_active,
        actor_id=actor_user_id,
    )
    session.commit()
    session.refresh(organization)
    return organization


def upsert_organization_as_admin(
    *,
    session: Session,
    payload: OrganizationCreateAdminRequest,
    actor_user_id: int,
) -> Organization:
    """Create or update an organization on behalf of an administrator.

    Parameters
    ----------
    session : Session
        Active database session used for the operation.
    payload : OrganizationCreateAdminRequest
        Organization creation or update data.
    actor_user_id : int
        Internal ID of the administrator performing the operation.

    Returns
    -------
    Organization
        The created or updated organization.

    Raises
    ------
    OrganizationTypeNotFoundException
        If the requested organization type does not exist.
    UserNotFoundException
        If a new organization's owner does not exist.
    UserRoleMismatchForOrganizationException
        If a new organization's owner is not an OWNER.
    OrganizationNotFoundException
        If an update targets a missing or inactive organization.
    AddressNotFoundException
        If an existing organization does not reference an address.
    """
    organization_type = get_organization_type_by_guid(session=session, guid=payload.organization_type_guid)
    if organization_type is None or organization_type.id is None:
        raise OrganizationTypeNotFoundException()

    if payload.guid is None:
        owner_replica = get_user_replica_by_guid(session=session, guid=str(payload.owner_user_guid))
        if owner_replica is None:
            raise UserNotFoundException()
        if owner_replica.role != UserType.OWNER:
            raise UserRoleMismatchForOrganizationException()
        if owner_replica.id is None:
            raise UserNotFoundException()

        return create_organization_with_owner(
            session=session,
            name=payload.name,
            description=payload.description,
            organization_type_id=organization_type.id,
            address_input=payload.address,
            owner_user_id=owner_replica.id,
            actor_user_id=actor_user_id,
        )

    organization = get_organization_by_guid(session=session, guid=payload.guid)
    if organization is None or organization.id is None or not organization.is_active:
        raise OrganizationNotFoundException()

    # owner_user_guid is intentionally ignored on update — ownership
    # transfer is performed via /organization/owner.
    return _update_organization_full(
        session=session,
        organization=organization,
        name=payload.name,
        description=payload.description,
        organization_type_id=organization_type.id,
        address_input=payload.address,
        is_active=payload.is_active,
        actor_user_id=actor_user_id,
    )


def upsert_organization_as_owner(
    *,
    session: Session,
    payload: OrganizationCreateOwnerRequest,
    actor_user_id: int,
) -> Organization:
    """Create or update an organization on behalf of its owner.

    Parameters
    ----------
    session : Session
        Active database session used for the operation.
    payload : OrganizationCreateOwnerRequest
        Organization creation or update data.
    actor_user_id : int
        Internal ID of the owner performing the operation.

    Returns
    -------
    Organization
        The created or updated organization.

    Raises
    ------
    OrganizationTypeNotFoundException
        If the requested organization type does not exist.
    OrganizationNotFoundException
        If an update targets a missing or inactive organization.
    OrganizationAccessForbiddenException
        If the actor is not an active owner of the organization.
    AddressNotFoundException
        If an existing organization does not reference an address.
    """
    organization_type = get_organization_type_by_guid(session=session, guid=payload.organization_type_guid)
    if organization_type is None or organization_type.id is None:
        raise OrganizationTypeNotFoundException()

    if payload.guid is None:
        return create_organization_with_owner(
            session=session,
            name=payload.name,
            description=payload.description,
            organization_type_id=organization_type.id,
            address_input=payload.address,
            owner_user_id=actor_user_id,
            actor_user_id=actor_user_id,
        )

    organization = get_organization_by_guid(session=session, guid=payload.guid)
    if organization is None or organization.id is None or not organization.is_active:
        raise OrganizationNotFoundException()

    if not is_user_active_owner_of_organization(
        session=session, organization_id=organization.id, user_id=actor_user_id
    ):
        raise OrganizationAccessForbiddenException()

    return _update_organization_full(
        session=session,
        organization=organization,
        name=payload.name,
        description=payload.description,
        organization_type_id=organization_type.id,
        address_input=payload.address,
        is_active=payload.is_active,
        actor_user_id=actor_user_id,
    )


def check_organization_deletable(*, session: Session, organization_id: int) -> None:  # noqa: ARG001
    """
    Extensibility hook for forward-looking dependency checks. Booking
    Service does not yet have bookings/properties/payments tables — extend
    this with a check per dependency (each raising
    OrganizationHasActiveDependenciesException) as those tables land.
    Active OWNER/MANAGER mappings are intentionally NOT checked here:
    deleting the organization makes the "must have an active owner"
    invariant moot, and mapping rows are kept as historical record.

    Parameters
    ----------
    session : Session
        Active database session reserved for future dependency checks.
    organization_id : int
        Internal ID of the organization to validate.

    Returns
    -------
    None
        No dependency checks are currently required.
    """
    return


def delete_organization(
    *,
    session: Session,
    guid: UUID,
    actor_user_id: int,
    requesting_user_id: int,
    is_admin: bool,
) -> None:
    """
    Soft-delete an organization (idempotent — already-deleted looks like
    not-found). Owners may only delete organizations they actively own.

    Parameters
    ----------
    session : Session
        Active database session used to persist the deletion.
    guid : UUID
        External organization GUID to delete.
    actor_user_id : int
        Internal ID of the user performing the deletion.
    requesting_user_id : int
        Internal ID of the user requesting the deletion.
    is_admin : bool
        Whether the requesting user has administrator privileges.

    Returns
    -------
    None
        The organization is soft-deleted in the current transaction.

    Raises
    ------
    OrganizationNotFoundException
        If the organization does not exist or is already inactive.
    OrganizationAccessForbiddenException
        If a non-administrator does not actively own the organization.
    """
    organization = get_organization_by_guid(session=session, guid=guid)
    if organization is None or organization.id is None or not organization.is_active:
        raise OrganizationNotFoundException()

    if not is_admin and not is_user_active_owner_of_organization(
        session=session, organization_id=organization.id, user_id=requesting_user_id
    ):
        raise OrganizationAccessForbiddenException()

    check_organization_deletable(session=session, organization_id=organization.id)
    soft_delete_organization(session=session, organization=organization, actor_id=actor_user_id)


def get_organization(
    *,
    session: Session,
    guid: UUID,
    requesting_user_id: int,
    role: UserType,
) -> Organization:
    """
    Fetch a single organization by guid, enforcing the same visibility
    rules as the role-scoped listing endpoints: Admins may view any
    organization; Owners/Managers may only view organizations they are
    actively associated with.

    Parameters
    ----------
    session : Session
        Active database session used to query the organization.
    guid : UUID
        External organization GUID to fetch.
    requesting_user_id : int
        Internal ID of the user requesting the organization.
    role : UserType
        Role used to determine visibility permissions.

    Returns
    -------
    Organization
        The requested active organization.

    Raises
    ------
    OrganizationNotFoundException
        If the organization does not exist or is inactive.
    OrganizationAccessForbiddenException
        If the requester is not authorized to view the organization.
    """
    organization = get_organization_by_guid(session=session, guid=guid)
    if organization is None or organization.id is None or not organization.is_active:
        raise OrganizationNotFoundException()

    if role == UserType.ADMIN:
        return organization

    if role == UserType.OWNER:
        if not is_user_active_owner_of_organization(
            session=session, organization_id=organization.id, user_id=requesting_user_id
        ):
            raise OrganizationAccessForbiddenException()
        return organization

    if not is_user_active_manager_of_organization(
        session=session, organization_id=organization.id, user_id=requesting_user_id
    ):
        raise OrganizationAccessForbiddenException()
    return organization


def _to_member_summary(user: UsersReplica | None) -> OrganizationMemberSummary | None:
    """Convert a user replica into the API member summary shape.

    Parameters
    ----------
    user : UsersReplica | None
        User replica to convert, or ``None`` when no member is available.

    Returns
    -------
    OrganizationMemberSummary | None
        Summary data for the user, or ``None`` when no user was supplied.

    Raises
    ------
    UserNotFoundException
        If the user exists but has no externally exposed GUID.
    """
    if user is None:
        return None
    user_guid = user.guid
    if user_guid is None:
        raise UserNotFoundException()
    return OrganizationMemberSummary(
        guid=user_guid,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        email=user.email,
    )


def build_organization_response(*, session: Session, organization: Organization) -> OrganizationResponse:
    """Build an API response from an organization and related members.

    Parameters
    ----------
    session : Session
        Active database session used to load related user replicas.
    organization : Organization
        Organization model to serialize.

    Returns
    -------
    OrganizationResponse
        API response containing organization, address, owner, and audit data.

    Raises
    ------
    SQLAlchemyError
        If related users cannot be loaded from the database.
    ValidationError
        If related model data cannot be validated into an API schema.
    OrganizationNotFoundException
        If the organization has no internal ID.
    """
    organization_id = organization.id
    if organization_id is None:
        raise OrganizationNotFoundException()
    organization_guid = organization.guid
    if organization_guid is None:
        raise OrganizationNotFoundException()

    owner_mapping = get_active_owner_mapping(session=session, organization_id=organization_id)
    owner = get_user_replica_by_id(session=session, user_id=owner_mapping.user_id) if owner_mapping else None
    created_by = get_user_replica_by_id(session=session, user_id=organization.created_by)
    updated_by = get_user_replica_by_id(session=session, user_id=organization.updated_by)

    return OrganizationResponse(
        guid=organization_guid,
        name=organization.name,
        description=organization.description,
        is_active=organization.is_active,
        organization_type=OrganizationTypeResponse.model_validate(
            organization.organization_type, from_attributes=True
        ),
        address=AddressResponse.model_validate(organization.address, from_attributes=True),
        owner=_to_member_summary(owner),
        created_by=_to_member_summary(created_by),
        updated_by=_to_member_summary(updated_by),
        created_at=organization.created_at,
        updated_at=organization.updated_at,
    )


def list_organizations_as_admin(
    *, session: Session, query: OrganizationListQueryParams
) -> OrganizationListResponse:
    """List organizations visible to an administrator.

    Parameters
    ----------
    session : Session
        Active database session used to query organizations.
    query : OrganizationListQueryParams
        Filtering, sorting, and pagination parameters.

    Returns
    -------
    OrganizationListResponse
        Paginated organization results.
    """
    return list_organizations_for_admin(session=session, query=query)


def list_organizations_as_owner(
    *, session: Session, owner_user_id: int, query: OrganizationListQueryParams
) -> OrganizationListResponse:
    """List organizations actively owned by a user.

    Parameters
    ----------
    session : Session
        Active database session used to query organizations.
    owner_user_id : int
        Internal ID of the owner whose organizations should be listed.
    query : OrganizationListQueryParams
        Filtering, sorting, and pagination parameters.

    Returns
    -------
    OrganizationListResponse
        Paginated organization results.
    """
    return list_organizations_for_owner(session=session, owner_user_id=owner_user_id, query=query)


def list_organizations_as_manager(
    *, session: Session, manager_user_id: int, query: OrganizationListQueryParams
) -> OrganizationListResponse:
    """List organizations actively managed by a user.

    Parameters
    ----------
    session : Session
        Active database session used to query organizations.
    manager_user_id : int
        Internal ID of the manager whose organizations should be listed.
    query : OrganizationListQueryParams
        Filtering, sorting, and pagination parameters.

    Returns
    -------
    OrganizationListResponse
        Paginated organization results.
    """
    return list_organizations_for_manager(session=session, manager_user_id=manager_user_id, query=query)


def list_organization_memberships(*, session: Session, user_id: int) -> OrganizationMembershipListResponse:
    """List every active organization a user is actively mapped to.

    Used by the client to resolve the caller's active organization, so the
    result is not paginated.

    Parameters
    ----------
    session : Session
        Active database session used to query organizations.
    user_id : int
        Internal ID of the user whose memberships should be listed.

    Returns
    -------
    OrganizationMembershipListResponse
        Organizations sorted by name; empty when the user has none.
    """
    return OrganizationMembershipListResponse(
        items=list_active_member_organizations(session=session, user_id=user_id)
    )


def resolve_active_organization(
    *, session: Session, user_guid: str, organization_guid: UUID
) -> ActiveOrganization:
    """Validate the active organization supplied by a caller.

    The organization must exist, be active, and the caller must hold an
    active mapping to it. Every failure raises the same exception so the
    response never reveals whether an organization exists.

    Parameters
    ----------
    session : Session
        Active database session used to query the user and organization.
    user_guid : str
        External GUID of the authenticated caller.
    organization_guid : UUID
        Active organization GUID sent by the caller.

    Returns
    -------
    ActiveOrganization
        The resolved organization (internal ID and GUID).

    Raises
    ------
    ActiveOrganizationInvalidException
        If the caller is unknown, or the organization is missing, inactive,
        or not actively mapped to the caller.
    """
    user = get_user_replica_by_guid(session=session, guid=user_guid)
    organization = None
    if user is not None and user.id is not None:
        organization = get_active_member_organization(
            session=session, user_id=user.id, organization_guid=organization_guid
        )

    if organization is None or organization.id is None:
        log.debug(
            "Active organization rejected user_guid=%s organization_guid=%s",
            user_guid,
            organization_guid,
        )
        raise ActiveOrganizationInvalidException()

    return ActiveOrganization(id=organization.id, guid=organization.guid)


def get_active_organization_summary(
    *, session: Session, active_organization: ActiveOrganization
) -> OrganizationMembershipSummary:
    """Build the summary of an already-validated active organization.

    Parameters
    ----------
    session : Session
        Active database session used to query the organization.
    active_organization : ActiveOrganization
        Organization resolved by `ActiveOrganizationDep`.

    Returns
    -------
    OrganizationMembershipSummary
        Summary used by the client to display the active organization.

    Raises
    ------
    ActiveOrganizationInvalidException
        If the organization disappeared after it was resolved.
    """
    summary = get_organization_membership_summary(session=session, organization_id=active_organization.id)
    if summary is None:
        raise ActiveOrganizationInvalidException()
    return summary
