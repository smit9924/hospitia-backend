from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from booking.api.dependencies import OrganizationScopedActorDep, SessionDep
from booking.api.services.room_type_service import (
    delete_room_type,
    get_room_type,
    list_room_types,
    upsert_room_type,
)
from booking.doc.not_found_exceptions_doc import NOT_FOUND_EXCEPTIONS_DOC
from booking.doc.security_exceptions_doc import SECURITY_EXCEPTION_DOC
from booking.doc.validation_exception_doc import VALIDATION_EXCEPTION_DOC
from booking.schemas.organization_schemas import OrganizationScopedActor
from booking.schemas.room_type_schemas import (
    RoomTypeListQueryParams,
    RoomTypeListResponse,
    RoomTypeResponse,
    RoomTypeUpsertRequest,
)
from booking.types.enums import UserType

_ADMIN_OWNER_MANAGER = [UserType.ADMIN, UserType.OWNER, UserType.MANAGER]

# Admins act on any organization; owners and managers are scoped to the
# active organization sent in the X-Active-Organization-Guid header.
_RoomTypeActorDep = Annotated[OrganizationScopedActor, Depends(OrganizationScopedActorDep(_ADMIN_OWNER_MANAGER))]

router = APIRouter(tags=["room-type"])

_AUTH_RESPONSES = {
    **SECURITY_EXCEPTION_DOC["UserUnauthorizedException"],
    **SECURITY_EXCEPTION_DOC["InvalidTokenException"],
    **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"],
    **VALIDATION_EXCEPTION_DOC["ActiveOrganizationRequiredException"],
    **SECURITY_EXCEPTION_DOC["ActiveOrganizationInvalidException"],
}

_UPSERT_RESPONSES = {
    **_AUTH_RESPONSES,
    **NOT_FOUND_EXCEPTIONS_DOC["RoomTypeNotFoundException"],
    **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"],
    **NOT_FOUND_EXCEPTIONS_DOC["CurrencyUnitNotFoundException"],
    **VALIDATION_EXCEPTION_DOC["RoomTypeAlreadyExistsException"],
    # Both 400 responses share one status code; the docs show the amenity one.
    **VALIDATION_EXCEPTION_DOC["RoomTypeOrganizationRequiredException"],
    **VALIDATION_EXCEPTION_DOC["RoomTypeAmenityNotAvailableException"],
}


@router.post("/create", responses=_UPSERT_RESPONSES)
@router.put("/create", responses=_UPSERT_RESPONSES)
async def upsert_room_type_route(
    session: SessionDep,
    payload: RoomTypeUpsertRequest,
    actor: _RoomTypeActorDep,
) -> RoomTypeResponse:
    """
    Create a room type, or update the one identified by `guid`.

    Admins must pass `organizationGuid` when creating; owners and managers
    create room types in their active organization. `amenityGuids`
    replaces the room type's amenities.
    """
    return upsert_room_type(session=session, actor=actor, payload=payload)


@router.delete("/delete", status_code=204, responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["RoomTypeNotFoundException"]})
async def delete_room_type_route(
    session: SessionDep,
    guid: Annotated[UUID, Query()],
    actor: _RoomTypeActorDep,
) -> None:
    """
    Soft-delete a room type.
    """
    delete_room_type(session=session, actor=actor, guid=guid)


@router.get("", responses={**_AUTH_RESPONSES})
async def list_room_types_route(
    session: SessionDep,
    query: Annotated[RoomTypeListQueryParams, Query()],
    actor: _RoomTypeActorDep,
) -> RoomTypeListResponse:
    """
    Return a paginated, sortable, searchable list of room types: every
    active organization's for admins; the active organization's for
    owners and managers.
    """
    return list_room_types(session=session, actor=actor, query=query)


@router.get("/{guid}", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["RoomTypeNotFoundException"]})
async def get_room_type_route(
    session: SessionDep,
    guid: UUID,
    actor: _RoomTypeActorDep,
) -> RoomTypeResponse:
    """
    Fetch a single room type visible to the caller.
    """
    return get_room_type(session=session, actor=actor, guid=guid)
