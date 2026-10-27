from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from booking.api.dependencies import (
    ActiveOrganizationDep,
    RoleValidationDep,
    SessionDep,
)
from booking.api.services.organization_service import (
    _resolve_actor,
    build_organization_response,
    delete_organization,
    get_active_organization_summary,
    get_organization,
    list_organization_memberships,
    list_organizations_as_admin,
    list_organizations_as_manager,
    list_organizations_as_owner,
    upsert_organization_as_admin,
    upsert_organization_as_owner,
)
from booking.api.services.organization_user_mapping_service import (
    assign_manager,
    assign_membership_as_admin,
    assign_owner,
    build_mapping_response,
)
from booking.doc.not_found_exceptions_doc import NOT_FOUND_EXCEPTIONS_DOC
from booking.doc.security_exceptions_doc import SECURITY_EXCEPTION_DOC
from booking.doc.validation_exception_doc import VALIDATION_EXCEPTION_DOC
from booking.schemas.auth_schemas import ParsedJWTPayload
from booking.schemas.organization_schemas import (
    ActiveOrganization,
    OrganizationAdminMappingRequest,
    OrganizationCreateAdminRequest,
    OrganizationCreateOwnerRequest,
    OrganizationListQueryParams,
    OrganizationListResponse,
    OrganizationManagerMappingRequest,
    OrganizationMappingResponse,
    OrganizationMembershipListResponse,
    OrganizationMembershipSummary,
    OrganizationOwnerMappingRequest,
    OrganizationResponse,
)
from booking.types.enums import UserType

_ADMIN_ONLY = [UserType.ADMIN]
_OWNER_ONLY = [UserType.OWNER]
_ADMIN_OWNER = [UserType.ADMIN, UserType.OWNER]
_ADMIN_OWNER_MANAGER = [UserType.ADMIN, UserType.OWNER, UserType.MANAGER]
_OWNER_MANAGER = [UserType.OWNER, UserType.MANAGER]

router = APIRouter(tags=["organization"])

_AUTH_RESPONSES = {
    **SECURITY_EXCEPTION_DOC["UserUnauthorizedException"],
    **SECURITY_EXCEPTION_DOC["InvalidTokenException"],
}


@router.post("/create-by-admin", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationTypeNotFoundException"], **VALIDATION_EXCEPTION_DOC["UserRoleMismatchForOrganizationException"]})
@router.put("/create-by-admin", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationTypeNotFoundException"], **VALIDATION_EXCEPTION_DOC["UserRoleMismatchForOrganizationException"]})
async def upsert_organization_admin_route(
    session: SessionDep,
    payload: OrganizationCreateAdminRequest,
    token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> OrganizationResponse:
    """
    Create or update an organization as an Admin. On create, `ownerUserGuid`
    is required and establishes the organization's initial OWNER mapping.
    """
    actor_user_id = _resolve_actor(session=session, guid=token.parsed_subject.user_guid)
    organization = upsert_organization_as_admin(session=session, payload=payload, actor_user_id=actor_user_id)
    return build_organization_response(session=session, organization=organization)


@router.post("/create-by-owner", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationTypeNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"], **SECURITY_EXCEPTION_DOC["OrganizationAccessForbiddenException"]})
@router.put("/create-by-owner", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationTypeNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"], **SECURITY_EXCEPTION_DOC["OrganizationAccessForbiddenException"]})
async def upsert_organization_owner_route(
    session: SessionDep,
    payload: OrganizationCreateOwnerRequest,
    token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_OWNER_ONLY))],
) -> OrganizationResponse:
    """
    Create or update an organization as its Owner. On create, the
    authenticated Owner is automatically associated as OWNER.
    """
    actor_user_id = _resolve_actor(session=session, guid=token.parsed_subject.user_guid)
    organization = upsert_organization_as_owner(session=session, payload=payload, actor_user_id=actor_user_id)
    return build_organization_response(session=session, organization=organization)


@router.delete("/delete", status_code=204, responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"], **SECURITY_EXCEPTION_DOC["OrganizationAccessForbiddenException"], **VALIDATION_EXCEPTION_DOC["OrganizationHasActiveDependenciesException"], **VALIDATION_EXCEPTION_DOC["OrganizationMustHaveActiveOwnerException"]})
async def delete_organization_route(
    session: SessionDep,
    guid: Annotated[UUID, Query()],
    token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_OWNER))],
) -> None:
    """
    Soft-delete an organization. Admins may delete any organization; Owners
    may only delete organizations they actively own.
    """
    actor_user_id = _resolve_actor(session=session, guid=token.parsed_subject.user_guid)
    delete_organization(
        session=session,
        guid=guid,
        actor_user_id=actor_user_id,
        requesting_user_id=actor_user_id,
        is_admin=token.parsed_subject.role == UserType.ADMIN,
    )


@router.get("/list-for-admin", responses={**_AUTH_RESPONSES})
async def list_organizations_admin_route(
    session: SessionDep,
    query: Annotated[OrganizationListQueryParams, Query()],
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> OrganizationListResponse:
    """
    List all organizations in the system for an admin user.
    """
    return list_organizations_as_admin(session=session, query=query)


@router.post("/admin", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"], **VALIDATION_EXCEPTION_DOC["UserRoleMismatchForOrganizationException"]})
@router.put("/admin", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"], **VALIDATION_EXCEPTION_DOC["UserRoleMismatchForOrganizationException"]})
async def upsert_admin_membership_route(
    session: SessionDep,
    payload: OrganizationAdminMappingRequest,
    token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> OrganizationMappingResponse:
    """
    Admin-only umbrella endpoint: assign/replace the OWNER or MANAGER
    mapping on any organization.
    """
    actor_user_id = _resolve_actor(session=session, guid=token.parsed_subject.user_guid)
    mapping, organization_guid = assign_membership_as_admin(session=session, payload=payload, actor_user_id=actor_user_id)
    return build_mapping_response(session=session, mapping=mapping, organization_guid=organization_guid)


@router.get("/list-for-owner", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"]})
async def list_organizations_owner_route(
    session: SessionDep,
    query: Annotated[OrganizationListQueryParams, Query()],
    token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_OWNER))],
) -> OrganizationListResponse:
    """
    List organizations the caller actively owns. Admins get all
    organizations (parity with `/list-for-admin`); Owners are scoped to themselves.
    """
    if token.parsed_subject.role == UserType.ADMIN:
        return list_organizations_as_admin(session=session, query=query)
    actor_user_id = _resolve_actor(session=session, guid=token.parsed_subject.user_guid)
    return list_organizations_as_owner(session=session, owner_user_id=actor_user_id, query=query)


@router.post("/owner", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"], **VALIDATION_EXCEPTION_DOC["UserRoleMismatchForOrganizationException"]})
@router.put("/owner", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"], **VALIDATION_EXCEPTION_DOC["UserRoleMismatchForOrganizationException"]})
async def upsert_owner_mapping_route(
    session: SessionDep,
    payload: OrganizationOwnerMappingRequest,
    token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> OrganizationMappingResponse:
    """
    Assign/replace the OWNER mapping (ownership transfer) on an
    organization. Admin-only — an Owner can never reassign their own
    organization's ownership.
    """
    actor_user_id = _resolve_actor(session=session, guid=token.parsed_subject.user_guid)
    mapping, organization_guid = assign_owner(session=session, payload=payload, actor_user_id=actor_user_id)
    return build_mapping_response(session=session, mapping=mapping, organization_guid=organization_guid)


@router.get("/manager", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"]})
async def list_organizations_manager_route(
    session: SessionDep,
    query: Annotated[OrganizationListQueryParams, Query()],
    token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_OWNER_MANAGER))],
) -> OrganizationListResponse:
    """
    List organizations the caller is an active MANAGER of. Admins get all
    organizations; Owners get organizations they own; Managers are scoped
    to themselves.
    """
    if token.parsed_subject.role == UserType.ADMIN:
        return list_organizations_as_admin(session=session, query=query)
    actor_user_id = _resolve_actor(session=session, guid=token.parsed_subject.user_guid)
    if token.parsed_subject.role == UserType.OWNER:
        return list_organizations_as_owner(session=session, owner_user_id=actor_user_id, query=query)
    return list_organizations_as_manager(session=session, manager_user_id=actor_user_id, query=query)


@router.post("/manager", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"], **SECURITY_EXCEPTION_DOC["OrganizationAccessForbiddenException"], **VALIDATION_EXCEPTION_DOC["UserRoleMismatchForOrganizationException"]})
@router.put("/manager", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"], **SECURITY_EXCEPTION_DOC["OrganizationAccessForbiddenException"], **VALIDATION_EXCEPTION_DOC["UserRoleMismatchForOrganizationException"]})
async def upsert_manager_mapping_route(
    session: SessionDep,
    payload: OrganizationManagerMappingRequest,
    token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_OWNER))],
) -> OrganizationMappingResponse:
    """
    Assign or remove a MANAGER mapping on an organization. Admin may act on
    any organization; Owner is restricted server-side to organizations they
    actively own. Managers cannot call this endpoint (read-only).
    """
    actor_user_id = _resolve_actor(session=session, guid=token.parsed_subject.user_guid)
    mapping, organization_guid = assign_manager(
        session=session,
        payload=payload,
        actor_user_id=actor_user_id,
        requesting_user_id=actor_user_id,
        is_admin=token.parsed_subject.role == UserType.ADMIN,
    )
    return build_mapping_response(session=session, mapping=mapping, organization_guid=organization_guid)


@router.get("/memberships", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"]})
async def list_organization_memberships_route(
    session: SessionDep,
    token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_OWNER_MANAGER))],
) -> OrganizationMembershipListResponse:
    """
    List every active organization the caller (Owner or Manager) is
    actively mapped to, sorted by name. Not paginated: the client uses it
    to resolve the caller's active organization.
    """
    actor_user_id = _resolve_actor(session=session, guid=token.parsed_subject.user_guid)
    return list_organization_memberships(session=session, user_id=actor_user_id)


@router.get("/active", responses={**_AUTH_RESPONSES, **VALIDATION_EXCEPTION_DOC["ActiveOrganizationRequiredException"], **SECURITY_EXCEPTION_DOC["ActiveOrganizationInvalidException"]})
async def get_active_organization_route(
    session: SessionDep,
    active_organization: Annotated[ActiveOrganization, Depends(ActiveOrganizationDep(_OWNER_MANAGER))],
) -> OrganizationMembershipSummary:
    """
    Validate the caller's active organization (sent in the
    `X-Active-Organization-Guid` header) and return its summary.
    """
    return get_active_organization_summary(session=session, active_organization=active_organization)


# NOTE: this catch-all-guid route must stay LAST in the router — Starlette
# matches routes in registration order, and "/{guid}" would otherwise shadow
# the static "/admin", "/owner", "/manager", "/delete", "/memberships" and
# "/active" paths above.
@router.get("/{guid}", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"], **SECURITY_EXCEPTION_DOC["OrganizationAccessForbiddenException"]})
async def get_organization_route(
    session: SessionDep,
    guid: UUID,
    token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_OWNER_MANAGER))],
) -> OrganizationResponse:
    """
    Fetch a single organization by guid. Admins may view any organization;
    Owners/Managers may only view organizations they are actively
    associated with.
    """
    actor_user_id = _resolve_actor(session=session, guid=token.parsed_subject.user_guid)
    organization = get_organization(
        session=session,
        guid=guid,
        requesting_user_id=actor_user_id,
        role=token.parsed_subject.role,
    )
    return build_organization_response(session=session, organization=organization)
