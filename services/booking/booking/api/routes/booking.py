from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from booking.api.dependencies import OrganizationScopedActorDep, SessionDep
from booking.api.services.booking_service import (
    cancel_booking,
    check_in_booking,
    check_out_booking,
    create_booking,
    get_booking,
    get_today_summary,
    list_available_rooms,
    list_bookings,
    update_booking,
)
from booking.doc.not_found_exceptions_doc import NOT_FOUND_EXCEPTIONS_DOC
from booking.doc.security_exceptions_doc import SECURITY_EXCEPTION_DOC
from booking.doc.validation_exception_doc import VALIDATION_EXCEPTION_DOC
from booking.schemas.booking_schemas import (
    AvailableRoom,
    AvailableRoomsQueryParams,
    BookingCancelRequest,
    BookingCreateRequest,
    BookingDetailResponse,
    BookingListQueryParams,
    BookingListResponse,
    BookingTodayQueryParams,
    BookingTodaySummaryResponse,
    BookingTransitionRequest,
    BookingUpdateRequest,
)
from booking.schemas.organization_schemas import OrganizationScopedActor
from booking.types.enums import UserType

_ADMIN_OWNER_MANAGER = [UserType.ADMIN, UserType.OWNER, UserType.MANAGER]

# Admins act on any organization; owners and managers are scoped to the
# active organization sent in the X-Active-Organization-Guid header.
_BookingActorDep = Annotated[OrganizationScopedActor, Depends(OrganizationScopedActorDep(_ADMIN_OWNER_MANAGER))]

# The dashboard's "today" summary belongs to an organization's members only.
_BookingMemberActorDep = Annotated[
    OrganizationScopedActor,
    Depends(OrganizationScopedActorDep([UserType.OWNER, UserType.MANAGER])),
]

router = APIRouter(tags=["booking"])

_AUTH_RESPONSES = {
    **SECURITY_EXCEPTION_DOC["UserUnauthorizedException"],
    **SECURITY_EXCEPTION_DOC["InvalidTokenException"],
    **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"],
    **VALIDATION_EXCEPTION_DOC["ActiveOrganizationRequiredException"],
    **SECURITY_EXCEPTION_DOC["ActiveOrganizationInvalidException"],
}

_FOUND_RESPONSES = {**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["BookingNotFoundException"]}

# Responses sharing a status code are merged by the docs; one example is shown per code.
_SAVE_RESPONSES = {
    **_AUTH_RESPONSES,
    **NOT_FOUND_EXCEPTIONS_DOC["OrganizationNotFoundException"],
    **VALIDATION_EXCEPTION_DOC["BookingOrganizationRequiredException"],
    **VALIDATION_EXCEPTION_DOC["BookingInvalidDatesException"],
    **VALIDATION_EXCEPTION_DOC["BookingPrimaryGuestRequiredException"],
    **VALIDATION_EXCEPTION_DOC["BookingGuestCapacityExceededException"],
    **VALIDATION_EXCEPTION_DOC["BookingRoomUnavailableException"],
}

_UPDATE_RESPONSES = {
    **_SAVE_RESPONSES,
    **NOT_FOUND_EXCEPTIONS_DOC["BookingNotFoundException"],
    **VALIDATION_EXCEPTION_DOC["BookingNotEditableException"],
}

_TRANSITION_RESPONSES = {
    **_FOUND_RESPONSES,
    **VALIDATION_EXCEPTION_DOC["BookingInvalidStatusTransitionException"],
}


@router.post("/create", status_code=201, responses=_SAVE_RESPONSES)
async def create_booking_route(
    session: SessionDep,
    payload: BookingCreateRequest,
    actor: _BookingActorDep,
) -> BookingDetailResponse:
    """
    Create a booking for one room with its primary and secondary guests.
    Admins choose the organization with `organizationGuid`; owners and
    managers book in their active organization.
    """
    return create_booking(session=session, actor=actor, payload=payload)


@router.put("/update", responses=_UPDATE_RESPONSES)
async def update_booking_route(
    session: SessionDep,
    payload: BookingUpdateRequest,
    actor: _BookingActorDep,
) -> BookingDetailResponse:
    """
    Update the booking identified by `guid` with its complete guest list.
    What can change depends on the booking's status.
    """
    return update_booking(session=session, actor=actor, payload=payload)


@router.get("", responses=_AUTH_RESPONSES)
async def list_bookings_route(
    session: SessionDep,
    query: Annotated[BookingListQueryParams, Query()],
    actor: _BookingActorDep,
) -> BookingListResponse:
    """
    Return a paginated list of bookings, searchable by reference, primary
    guest name or phone, or room number, and filterable by status and stay
    dates: every active organization's for admins; the active
    organization's for owners and managers.
    """
    return list_bookings(session=session, actor=actor, query=query)


@router.get("/detail", responses=_FOUND_RESPONSES)
async def get_booking_route(
    session: SessionDep,
    guid: Annotated[UUID, Query()],
    actor: _BookingActorDep,
) -> BookingDetailResponse:
    """
    Fetch a booking with its guests (ID numbers in full) and its status history.
    """
    return get_booking(session=session, actor=actor, guid=guid)


@router.get(
    "/available-rooms",
    responses={
        **_FOUND_RESPONSES,
        **VALIDATION_EXCEPTION_DOC["BookingOrganizationRequiredException"],
        **VALIDATION_EXCEPTION_DOC["BookingInvalidDatesException"],
    },
)
async def list_available_rooms_route(
    session: SessionDep,
    query: Annotated[AvailableRoomsQueryParams, Query()],
    actor: _BookingActorDep,
) -> list[AvailableRoom]:
    """
    List the available rooms that are free for the stay, with their
    capacity and nightly cost.
    """
    return list_available_rooms(session=session, actor=actor, query=query)


@router.post("/check-in", responses=_TRANSITION_RESPONSES)
async def check_in_booking_route(
    session: SessionDep,
    payload: BookingTransitionRequest,
    actor: _BookingActorDep,
) -> BookingDetailResponse:
    """
    Check in the guests of a confirmed booking, from its check-in date.
    """
    return check_in_booking(session=session, actor=actor, payload=payload)


@router.post("/check-out", responses=_TRANSITION_RESPONSES)
async def check_out_booking_route(
    session: SessionDep,
    payload: BookingTransitionRequest,
    actor: _BookingActorDep,
) -> BookingDetailResponse:
    """
    Check out the guests of a checked-in booking. An early check-out moves
    the check-out date to today.
    """
    return check_out_booking(session=session, actor=actor, payload=payload)


@router.post("/cancel", responses=_TRANSITION_RESPONSES)
async def cancel_booking_route(
    session: SessionDep,
    payload: BookingCancelRequest,
    actor: _BookingActorDep,
) -> BookingDetailResponse:
    """
    Cancel a confirmed booking, with an optional reason.
    """
    return cancel_booking(session=session, actor=actor, payload=payload)


@router.get("/today-summary", responses=_AUTH_RESPONSES)
async def get_today_summary_route(
    session: SessionDep,
    query: Annotated[BookingTodayQueryParams, Query()],
    actor: _BookingMemberActorDep,
) -> BookingTodaySummaryResponse:
    """
    Count the active organization's arrivals, departures and in-house
    bookings on `onDate` (the caller's local date). Owners and managers only.
    """
    return get_today_summary(session=session, actor=actor, query=query)
