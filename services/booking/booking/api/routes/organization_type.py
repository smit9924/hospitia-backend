from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from booking.api.dependencies import RoleValidationDep, SessionDep
from booking.api.services.organization_service import _resolve_actor
from booking.api.services.organization_type_service import (
    delete_organization_type,
    get_organization_type,
    list_organization_types,
    upsert_organization_type,
)
from booking.doc.not_found_exceptions_doc import NOT_FOUND_EXCEPTIONS_DOC
from booking.doc.security_exceptions_doc import SECURITY_EXCEPTION_DOC
from booking.doc.validation_exception_doc import VALIDATION_EXCEPTION_DOC
from booking.schemas.auth_schemas import ParsedJWTPayload
from booking.schemas.organization_type_schemas import (
    OrganizationTypeListQueryParams,
    OrganizationTypeListResponse,
    OrganizationTypeResponse,
    OrganizationTypeUpsertRequest,
)
from booking.types.enums import UserType

_ADMIN_ONLY = [UserType.ADMIN]
_ADMIN_OWNER_ONLY = [UserType.ADMIN, UserType.OWNER]

router = APIRouter(tags=["organization-type"])


@router.post("/create", responses={**SECURITY_EXCEPTION_DOC["UserUnauthorizedException"], **SECURITY_EXCEPTION_DOC["InvalidTokenException"], **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **VALIDATION_EXCEPTION_DOC["OrganizationTypeAlreadyExistsException"]})
@router.put("/create", responses={**SECURITY_EXCEPTION_DOC["UserUnauthorizedException"], **SECURITY_EXCEPTION_DOC["InvalidTokenException"], **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **VALIDATION_EXCEPTION_DOC["OrganizationTypeAlreadyExistsException"]})
async def upsert_organization_type_route(
    session: SessionDep,
    payload: OrganizationTypeUpsertRequest,
    token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> OrganizationTypeResponse:
    """
    Create a new organization type, or update an existing one when `guid`
    is supplied. Admin-only.
    """
    actor_user_id = _resolve_actor(session=session, guid=token.parsed_subject.user_guid)
    return upsert_organization_type(session=session, payload=payload, actor_user_id=actor_user_id)


@router.delete("/delete", status_code=204, responses={**SECURITY_EXCEPTION_DOC["UserUnauthorizedException"], **SECURITY_EXCEPTION_DOC["InvalidTokenException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationTypeNotFoundException"], **VALIDATION_EXCEPTION_DOC["OrganizationTypeHasActiveOrganizationsException"]})
async def delete_organization_type_route(
    session: SessionDep,
    guid: Annotated[UUID, Query()],
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> None:
    """
    Delete an organization type identified by `guid`. Admin-only.
    """
    delete_organization_type(session=session, guid=guid)


@router.get("", responses={**SECURITY_EXCEPTION_DOC["UserUnauthorizedException"], **SECURITY_EXCEPTION_DOC["InvalidTokenException"]})
async def list_organization_types_route(
    session: SessionDep,
    query: Annotated[OrganizationTypeListQueryParams, Query()],
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_OWNER_ONLY))],
) -> OrganizationTypeListResponse:
    """
    Return a paginated, sortable, searchable list of organization types.
    Admin-only.
    """
    return list_organization_types(session=session, query=query)


@router.get("/{guid}", responses={**SECURITY_EXCEPTION_DOC["UserUnauthorizedException"], **SECURITY_EXCEPTION_DOC["InvalidTokenException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationTypeNotFoundException"]})
async def get_organization_type_route(
    session: SessionDep,
    guid: UUID,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> OrganizationTypeResponse:
    """
    Fetch a single organization type by guid. Admin-only.
    """
    return get_organization_type(session=session, guid=guid)
