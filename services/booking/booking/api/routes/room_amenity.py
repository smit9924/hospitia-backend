from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from booking.api.dependencies import OrganizationScopedActorDep, SessionDep
from booking.api.services.room_amenity_service import (
    delete_room_amenity,
    get_room_amenity,
    list_room_amenities,
    list_selectable_room_amenity_options,
    upsert_room_amenity,
)
from booking.doc.not_found_exceptions_doc import NOT_FOUND_EXCEPTIONS_DOC
from booking.doc.security_exceptions_doc import SECURITY_EXCEPTION_DOC
from booking.doc.validation_exception_doc import VALIDATION_EXCEPTION_DOC
from booking.schemas.organization_schemas import OrganizationScopedActor
from booking.schemas.room_amenity_schemas import (
    RoomAmenityListQueryParams,
    RoomAmenityListResponse,
    RoomAmenityOption,
    RoomAmenityResponse,
    RoomAmenitySelectableQueryParams,
    RoomAmenityUpsertRequest,
)
from booking.types.enums import UserType

_ADMIN_OWNER_MANAGER = [UserType.ADMIN, UserType.OWNER, UserType.MANAGER]

# Admins act on any organization; owners and managers are scoped to the
# active organization sent in the X-Active-Organization-Guid header.
_RoomAmenityActorDep = Annotated[OrganizationScopedActor, Depends(OrganizationScopedActorDep(_ADMIN_OWNER_MANAGER))]

router = APIRouter(tags=["room-amenity"])

_AUTH_RESPONSES = {
    **SECURITY_EXCEPTION_DOC["UserUnauthorizedException"],
    **SECURITY_EXCEPTION_DOC["InvalidTokenException"],
    **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"],
    **VALIDATION_EXCEPTION_DOC["ActiveOrganizationRequiredException"],
    **SECURITY_EXCEPTION_DOC["ActiveOrganizationInvalidException"],
}


@router.post("/create", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["RoomAmenityNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"], **SECURITY_EXCEPTION_DOC["RoomAmenityModificationForbiddenException"], **VALIDATION_EXCEPTION_DOC["RoomAmenityAlreadyExistsException"]})
@router.put("/create", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["RoomAmenityNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"], **SECURITY_EXCEPTION_DOC["RoomAmenityModificationForbiddenException"], **VALIDATION_EXCEPTION_DOC["RoomAmenityAlreadyExistsException"]})
async def upsert_room_amenity_route(
    session: SessionDep,
    payload: RoomAmenityUpsertRequest,
    actor: _RoomAmenityActorDep,
) -> RoomAmenityResponse:
    """
    Create a room amenity, or update the one identified by `guid`.

    Admins create a default amenity, or a custom one of `organizationGuid`.
    Owners and managers create custom amenities of their active
    organization and cannot change default amenities.
    """
    return upsert_room_amenity(session=session, actor=actor, payload=payload)


@router.delete("/delete", status_code=204, responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["RoomAmenityNotFoundException"], **SECURITY_EXCEPTION_DOC["RoomAmenityModificationForbiddenException"], **VALIDATION_EXCEPTION_DOC["RoomAmenityInUseException"]})
async def delete_room_amenity_route(
    session: SessionDep,
    guid: Annotated[UUID, Query()],
    actor: _RoomAmenityActorDep,
) -> None:
    """
    Soft-delete a room amenity. Rejected while an active room type uses it.
    Owners and managers may delete only their organization's custom amenities.
    """
    delete_room_amenity(session=session, actor=actor, guid=guid)


@router.get("", responses={**_AUTH_RESPONSES})
async def list_room_amenities_route(
    session: SessionDep,
    query: Annotated[RoomAmenityListQueryParams, Query()],
    actor: _RoomAmenityActorDep,
) -> RoomAmenityListResponse:
    """
    Return a paginated, sortable, searchable list of room amenities: every
    amenity for admins; the defaults plus the active organization's custom
    amenities for owners and managers.
    """
    return list_room_amenities(session=session, actor=actor, query=query)


@router.get("/selectable", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"]})
async def list_selectable_room_amenities_route(
    session: SessionDep,
    query: Annotated[RoomAmenitySelectableQueryParams, Query()],
    actor: _RoomAmenityActorDep,
) -> list[RoomAmenityOption]:
    """
    Return every amenity a room type of the organization may use (defaults
    plus that organization's custom amenities), ordered by name. Not
    paginated. Admins choose the organization with `organizationGuid`.
    """
    return list_selectable_room_amenity_options(
        session=session,
        actor=actor,
        organization_guid=query.organization_guid,
    )


@router.get("/{guid}", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["RoomAmenityNotFoundException"]})
async def get_room_amenity_route(
    session: SessionDep,
    guid: UUID,
    actor: _RoomAmenityActorDep,
) -> RoomAmenityResponse:
    """
    Fetch a single room amenity visible to the caller.
    """
    return get_room_amenity(session=session, actor=actor, guid=guid)
