from sqlmodel import Session

from booking.api.repositories.organization_repository import get_organization_by_guid
from booking.api.repositories.organization_user_mapping_repository import (
    get_active_owner_mapping,
    get_or_create_mapping,
    is_user_active_owner_of_organization,
)
from booking.api.repositories.user_repository import (
    get_user_replica_by_guid,
    get_user_replica_by_id,
)
from booking.database.models.organization_user_mapping import OrganizationUserMapping
from booking.exceptions.definitions.not_found_exceptions import (
    OrganizationNotFoundException,
    UserNotFoundException,
)
from booking.exceptions.definitions.security_exceptions import (
    OrganizationAccessForbiddenException,
)
from booking.exceptions.definitions.validation_exceptions import (
    UserRoleMismatchForOrganizationException,
)
from booking.schemas.organization_schemas import (
    OrganizationAdminMappingRequest,
    OrganizationManagerMappingRequest,
    OrganizationMappingResponse,
    OrganizationMemberSummary,
    OrganizationOwnerMappingRequest,
)
from booking.types.enums import OrganizationRole, UserType


def replace_owner_mapping(
    *,
    session: Session,
    organization_id: int,
    new_owner_user_id: int,
    actor_user_id: int,
) -> OrganizationUserMapping:
    """
    Assign/activate the OWNER mapping for `new_owner_user_id`, then
    deactivate the previous active OWNER mapping (if different). Ordered so
    the organization is never left without an active owner: the new mapping
    is flushed (constraint-checked) before the old one is deactivated, and
    both changes land in a single commit.
    """
    new_mapping = get_or_create_mapping(
        session=session,
        organization_id=organization_id,
        user_id=new_owner_user_id,
        role=OrganizationRole.OWNER,
        actor_id=actor_user_id,
    )
    new_mapping.is_active = True
    new_mapping.updated_by = actor_user_id
    session.add(new_mapping)
    session.flush()

    old_mapping = get_active_owner_mapping(session=session, organization_id=organization_id)
    if old_mapping is not None and old_mapping.user_id != new_owner_user_id:
        old_mapping.is_active = False
        old_mapping.updated_by = actor_user_id
        session.add(old_mapping)

    session.commit()
    session.refresh(new_mapping)
    return new_mapping


def upsert_manager_mapping(
    *,
    session: Session,
    organization_id: int,
    manager_user_id: int,
    is_active: bool,
    actor_user_id: int,
) -> OrganizationUserMapping:
    """
    Assign (`is_active=True`) or remove (`is_active=False`) a MANAGER
    mapping for an organization.
    """
    mapping = get_or_create_mapping(
        session=session,
        organization_id=organization_id,
        user_id=manager_user_id,
        role=OrganizationRole.MANAGER,
        actor_id=actor_user_id,
    )
    mapping.is_active = is_active
    mapping.updated_by = actor_user_id
    session.add(mapping)
    session.commit()
    session.refresh(mapping)
    return mapping


def assign_owner(
    *,
    session: Session,
    payload: OrganizationOwnerMappingRequest,
    actor_user_id: int,
) -> tuple[OrganizationUserMapping, str]:
    """
    Validate and replace the OWNER mapping on an organization. Admin-only
    (enforced at the route layer).
    """
    organization = get_organization_by_guid(session=session, guid=payload.organization_guid)
    if organization is None or not organization.is_active:
        raise OrganizationNotFoundException()

    new_owner = get_user_replica_by_guid(session=session, guid=str(payload.owner_user_guid))
    if new_owner is None:
        raise UserNotFoundException()
    if new_owner.role != UserType.OWNER:
        raise UserRoleMismatchForOrganizationException()

    mapping = replace_owner_mapping(
        session=session,
        organization_id=organization.id,
        new_owner_user_id=new_owner.id,
        actor_user_id=actor_user_id,
    )
    return mapping, str(organization.guid)


def assign_manager(
    *,
    session: Session,
    payload: OrganizationManagerMappingRequest,
    actor_user_id: int,
    requesting_user_id: int,
    is_admin: bool,
) -> tuple[OrganizationUserMapping, str]:
    """
    Validate and assign/remove a MANAGER mapping on an organization.
    Callable by Admin (any organization) or Owner (only their own
    organization, enforced here).
    """
    organization = get_organization_by_guid(session=session, guid=payload.organization_guid)
    if organization is None or not organization.is_active:
        raise OrganizationNotFoundException()

    if not is_admin and not is_user_active_owner_of_organization(
        session=session, organization_id=organization.id, user_id=requesting_user_id
    ):
        raise OrganizationAccessForbiddenException()

    manager = get_user_replica_by_guid(session=session, guid=str(payload.manager_user_guid))
    if manager is None:
        raise UserNotFoundException()
    if manager.role != UserType.MANAGER:
        raise UserRoleMismatchForOrganizationException()

    mapping = upsert_manager_mapping(
        session=session,
        organization_id=organization.id,
        manager_user_id=manager.id,
        is_active=payload.is_active,
        actor_user_id=actor_user_id,
    )
    return mapping, str(organization.guid)


def assign_membership_as_admin(
    *,
    session: Session,
    payload: OrganizationAdminMappingRequest,
    actor_user_id: int,
) -> tuple[OrganizationUserMapping, str]:
    """
    Admin-only umbrella mapping endpoint: assign/replace the OWNER or
    MANAGER mapping on any organization.
    """
    organization = get_organization_by_guid(session=session, guid=payload.organization_guid)
    if organization is None or not organization.is_active:
        raise OrganizationNotFoundException()

    user = get_user_replica_by_guid(session=session, guid=str(payload.user_guid))
    if user is None:
        raise UserNotFoundException()

    if payload.role == OrganizationRole.OWNER:
        if user.role != UserType.OWNER:
            raise UserRoleMismatchForOrganizationException()
        mapping = replace_owner_mapping(
            session=session,
            organization_id=organization.id,
            new_owner_user_id=user.id,
            actor_user_id=actor_user_id,
        )
    else:
        if user.role != UserType.MANAGER:
            raise UserRoleMismatchForOrganizationException()
        mapping = upsert_manager_mapping(
            session=session,
            organization_id=organization.id,
            manager_user_id=user.id,
            is_active=payload.is_active,
            actor_user_id=actor_user_id,
        )

    return mapping, str(organization.guid)


def build_mapping_response(
    *,
    session: Session,
    mapping: OrganizationUserMapping,
    organization_guid: str,
) -> OrganizationMappingResponse:
    user = get_user_replica_by_id(session=session, user_id=mapping.user_id)
    return OrganizationMappingResponse(
        guid=mapping.guid,
        organization_guid=organization_guid,
        user=OrganizationMemberSummary(
            guid=user.guid,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            email=user.email,
        ),
        role=OrganizationRole(user.role),
        is_active=mapping.is_active,
    )
