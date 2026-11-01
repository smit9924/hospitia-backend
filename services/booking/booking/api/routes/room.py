from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from booking.api.dependencies import OrganizationScopedActorDep, SessionDep
from booking.api.services.room_service import (
    create_room,
    delete_room,
    get_room,
    list_rooms,
    update_room,
)
from booking.doc.not_found_exceptions_doc import NOT_FOUND_EXCEPTIONS_DOC
from booking.doc.security_exceptions_doc import SECURITY_EXCEPTION_DOC
from booking.doc.validation_exception_doc import VALIDATION_EXCEPTION_DOC
from booking.schemas.organization_schemas import OrganizationScopedActor
from booking.schemas.room_schemas import (
    RoomCreateRequest,
    RoomListQueryParams,
    RoomListResponse,
    RoomResponse,
    RoomUpdateRequest,
)
from booking.types.enums import UserType

_ADMIN_OWNER_MANAGER = [UserType.ADMIN, UserType.OWNER, UserType.MANAGER]

# Admins act on any organization; owners and managers are scoped to the
# active organization sent in the X-Active-Organization-Guid header.
_RoomActorDep = Annotated[OrganizationScopedActor, Depends(OrganizationScopedActorDep(_ADMIN_OWNER_MANAGER))]

router = APIRouter(tags=["room"])

_AUTH_RESPONSES = {
    **SECURITY_EXCEPTION_DOC["UserUnauthorizedException"],
    **SECURITY_EXCEPTION_DOC["InvalidTokenException"],
    **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"],
    **VALIDATION_EXCEPTION_DOC["ActiveOrganizationRequiredException"],
    **SECURITY_EXCEPTION_DOC["ActiveOrganizationInvalidException"],
}

_CREATE_RESPONSES = {
    **_AUTH_RESPONSES,
    **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"],
    **VALIDATION_EXCEPTION_DOC["RoomAlreadyExistsException"],
    # Both 400 responses share one status code; the docs show the room type one.
    **VALIDATION_EXCEPTION_DOC["RoomOrganizationRequiredException"],
    **VALIDATION_EXCEPTION_DOC["RoomTypeNotAvailableForRoomException"],
}

_UPDATE_RESPONSES = {
    **_AUTH_RESPONSES,
    **NOT_FOUND_EXCEPTIONS_DOC["RoomNotFoundException"],
    **VALIDATION_EXCEPTION_DOC["RoomAlreadyExistsException"],
    **VALIDATION_EXCEPTION_DOC["RoomTypeNotAvailableForRoomException"],
}


@router.post("/create", responses=_CREATE_RESPONSES)
async def create_room_route(
    session: SessionDep,
    payload: RoomCreateRequest,
    actor: _RoomActorDep,
) -> RoomResponse:
    """
    Create a room. Admins choose the organization with `organizationGuid`;
    owners and managers create rooms in their active organization.
    """
    return create_room(session=session, actor=actor, payload=payload)


@router.put("/update", responses=_UPDATE_RESPONSES)
async def update_room_route(
    session: SessionDep,
    payload: RoomUpdateRequest,
    actor: _RoomActorDep,
) -> RoomResponse:
    """
    Update the room identified by `guid`. The organization never changes.
    """
    return update_room(session=session, actor=actor, payload=payload)


@router.delete("/delete", status_code=204, responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["RoomNotFoundException"]})
async def delete_room_route(
    session: SessionDep,
    guid: Annotated[UUID, Query()],
    actor: _RoomActorDep,
) -> None:
    """
    Soft-delete a room.
    """
    delete_room(session=session, actor=actor, guid=guid)


@router.get("", responses={**_AUTH_RESPONSES})
async def list_rooms_route(
    session: SessionDep,
    query: Annotated[RoomListQueryParams, Query()],
    actor: _RoomActorDep,
) -> RoomListResponse:
    """
    Return a paginated, sortable list of rooms searchable by room number:
    every active organization's for admins; the active organization's for
    owners and managers.
    """
    return list_rooms(session=session, actor=actor, query=query)


@router.get("/detail", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["RoomNotFoundException"]})
async def get_room_route(
    session: SessionDep,
    guid: Annotated[UUID, Query()],
    actor: _RoomActorDep,
) -> RoomResponse:
    """
    Fetch a single room visible to the caller.
    """
    return get_room(session=session, actor=actor, guid=guid)
