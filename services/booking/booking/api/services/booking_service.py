"""
Business rules for bookings.

A booking reserves one room of one organization for a stay (check-in date
up to, not including, the check-out date) and records its guests: exactly
one primary guest (the contact person, with phone and ID proof) and
secondary guests, never more than the room's capacity.

- Admins manage the bookings of every active organization and choose the
  organization when creating one.
- Owners and managers manage the bookings of their active organization
  only; other organizations' bookings are reported as not found.

Lifecycle: confirmed -> checked in -> checked out, or confirmed ->
cancelled. A room never holds two confirmed or checked-in bookings for
overlapping stays. The pure rules live in `booking_rules`; this module
applies them with the repositories and sends the guest emails after each
committed change.
"""

from collections import defaultdict
from datetime import UTC, date, datetime
from uuid import UUID

from sqlmodel import Session

from booking.api.repositories.booking_repository import (
    add_booking,
    count_today,
    get_booking_by_guid,
    has_active_bookings_for_room,
    has_overlapping_booking,
    list_bookings_around_date,
    list_bookings_page,
    next_booking_reference_number,
    room_booking_lock,
    save_booking,
)
from booking.api.repositories.booking_repository import (
    list_available_rooms as list_available_rooms_repo,
)
from booking.api.repositories.guest_repository import (
    BookingGuestEntry,
    list_booking_guests,
    replace_booking_guests,
)
from booking.api.repositories.room_repository import get_active_room_by_guid
from booking.api.repositories.user_repository import get_user_replica_by_id
from booking.api.services import booking_rules
from booking.api.services.booking_notification_service import (
    BookingStaySnapshot,
    send_booking_cancelled_email,
    send_booking_confirmed_email,
    send_booking_updated_email,
)
from booking.api.services.organization_service import (
    get_active_organization_or_raise,
    get_member_active_organization_id,
)
from booking.database.models.booking import Booking
from booking.database.models.booking_guest_mapping import BookingGuestMapping
from booking.database.models.guest_detail import GuestDetail
from booking.database.models.room import Room
from booking.database.models.users import UsersReplica
from booking.exceptions.definitions.not_found_exceptions import (
    BookingNotFoundException,
    UserNotFoundException,
)
from booking.exceptions.definitions.validation_exceptions import (
    BookingOrganizationRequiredException,
    BookingPrimaryGuestRequiredException,
    BookingRoomUnavailableException,
    RoomHasActiveBookingsException,
)
from booking.schemas.booking_schemas import (
    AvailableRoom,
    AvailableRoomsQueryParams,
    AvailableRoomTypeReference,
    BookingCancelRequest,
    BookingCreateRequest,
    BookingDetailResponse,
    BookingGuestResponse,
    BookingListItem,
    BookingListQueryParams,
    BookingListResponse,
    BookingPrimaryGuestSummary,
    BookingRoomReference,
    BookingRoomTypeReference,
    BookingStayInput,
    BookingTodayQueryParams,
    BookingTodaySummaryResponse,
    BookingTransitionRequest,
    BookingUpdateRequest,
    RoomOccupancy,
    UserReference,
)
from booking.schemas.currency_unit_schemas import CurrencyUnitOption
from booking.schemas.organization_schemas import (
    OrganizationReference,
    OrganizationScopedActor,
)
from booking.types.enums import BookingStatus, RoomStatus, UserType

_ROOM_STATUS_LABELS = {
    RoomStatus.UNDER_MAINTENANCE: "under maintenance",
    RoomStatus.OUT_OF_SERVICE: "out of service",
}


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------


def _to_user_reference(user: UsersReplica | None) -> UserReference | None:
    """Build the public reference of a user, if any."""
    if user is None:
        return None
    return UserReference(guid=user.guid, first_name=user.first_name, last_name=user.last_name)  # type: ignore[arg-type]


def _to_room_reference(room: Room) -> BookingRoomReference:
    """Build the reference of the booked room with its type and capacity."""
    return BookingRoomReference(
        guid=room.guid,  # type: ignore[arg-type]
        room_number=room.room_number,
        floor=room.floor,
        room_type=BookingRoomTypeReference(
            guid=room.room_type.guid,  # type: ignore[arg-type]
            name=room.room_type.name,
            capacity=room.room_type.capacity,
        ),
    )


def _to_guest_response(guest: GuestDetail, *, mask_id_proof: bool) -> BookingGuestResponse:
    """Build a guest response, masking the ID proof number when asked."""
    response = BookingGuestResponse.model_validate(guest, from_attributes=True)
    if mask_id_proof:
        response.id_proof_number = booking_rules.mask_id_proof_number(guest.id_proof_number)
    return response


def _summary_fields(booking: Booking, today: date) -> dict[str, object]:
    """Fields shared by the listing item and the details response."""
    return {
        "guid": booking.guid,
        "reference": booking.reference,
        "status": booking.status,
        "organization": OrganizationReference.model_validate(booking.organization, from_attributes=True),
        "room": _to_room_reference(booking.room),
        "check_in_date": booking.check_in_date,
        "check_out_date": booking.check_out_date,
        "nights": booking.nights,
        "guest_count": booking.guest_count,
        "cost_per_night": booking.cost_per_night,
        "total_amount": booking.total_amount,
        "currency": CurrencyUnitOption.model_validate(booking.currency_unit, from_attributes=True),
        "booked_by": _to_user_reference(booking.booker),
        "booked_by_role": booking.booked_by_role,
        "created_at": booking.created_at,
        "allowed_actions": booking_rules.allowed_actions(
            status=booking.status,
            check_in_date=booking.check_in_date,
            today=today,
        ),
    }


def _split_guests(mappings: list[BookingGuestMapping]) -> tuple[GuestDetail | None, list[GuestDetail]]:
    """Split a booking's guest mappings into its primary and secondary guests."""
    primary = next((mapping.guest for mapping in mappings if mapping.is_primary), None)
    secondary = [mapping.guest for mapping in mappings if not mapping.is_primary]
    return primary, secondary


def _to_detail_response(*, session: Session, booking: Booking) -> BookingDetailResponse:
    """Build the booking details: everything, with guests and full ID numbers."""
    primary, secondary = _split_guests(list_booking_guests(session=session, booking_ids=[booking.id]))  # type: ignore[list-item]
    return BookingDetailResponse(
        **_summary_fields(booking, booking_rules.utc_today()),  # type: ignore[arg-type]
        notes=booking.notes,
        updated_at=booking.updated_at,
        checked_in_at=booking.checked_in_at,
        checked_in_by=_to_user_reference(booking.checked_in_user),
        checked_out_at=booking.checked_out_at,
        checked_out_by=_to_user_reference(booking.checked_out_user),
        cancelled_at=booking.cancelled_at,
        cancelled_by=_to_user_reference(booking.cancelled_user),
        cancellation_reason=booking.cancellation_reason,
        primary_guest=_to_guest_response(primary, mask_id_proof=False) if primary else None,
        secondary_guests=[_to_guest_response(guest, mask_id_proof=False) for guest in secondary],
    )


def _to_list_item(booking: Booking, primary_guest: GuestDetail | None, today: date) -> BookingListItem:
    """Build a listing row; the primary guest's ID number is masked."""
    primary_summary = None
    if primary_guest is not None:
        primary_summary = BookingPrimaryGuestSummary(
            guid=primary_guest.guid,  # type: ignore[arg-type]
            first_name=primary_guest.first_name,
            last_name=primary_guest.last_name,
            phone=primary_guest.phone,
            id_proof_type=primary_guest.id_proof_type,
            id_proof_number=booking_rules.mask_id_proof_number(primary_guest.id_proof_number),
        )
    return BookingListItem(**_summary_fields(booking, today), primary_guest=primary_summary)  # type: ignore[arg-type]


def _primary_guest_of(*, session: Session, booking: Booking) -> GuestDetail | None:
    """Return the booking's primary guest."""
    primary, _ = _split_guests(list_booking_guests(session=session, booking_ids=[booking.id]))  # type: ignore[list-item]
    return primary


# ---------------------------------------------------------------------------
# Lookups and checks
# ---------------------------------------------------------------------------


def _resolve_organization_id(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    organization_guid: UUID | None,
) -> int:
    """Decide the organization a new booking (or room search) belongs to.

    Owners and managers use their active organization; admins must choose one.

    Raises
    ------
    BookingOrganizationRequiredException
        If an admin does not choose an organization.
    OrganizationNotFoundException
        If an admin chooses a missing or inactive organization.
    """
    if not actor.is_admin:
        return get_member_active_organization_id(actor)
    if organization_guid is None:
        raise BookingOrganizationRequiredException()
    return get_active_organization_or_raise(session=session, guid=organization_guid).id  # type: ignore[return-value]


def _get_visible_booking_or_raise(*, session: Session, actor: OrganizationScopedActor, guid: UUID) -> Booking:
    """Fetch a booking the actor may manage.

    Raises
    ------
    BookingNotFoundException
        If the booking does not exist, belongs to a deleted organization, or
        belongs to another organization than an owner's or manager's active one.
    """
    booking = get_booking_by_guid(session=session, guid=guid)
    if booking is None or not booking.organization.is_active:
        raise BookingNotFoundException()
    if not actor.is_admin and booking.organization_id != get_member_active_organization_id(actor):
        raise BookingNotFoundException()
    return booking


def _get_bookable_room_or_raise(
    *,
    session: Session,
    room_guid: UUID,
    organization_id: int,
    current_room_id: int | None,
) -> Room:
    """Fetch the room chosen for a booking.

    A newly chosen room must be available; a booking keeps its current room
    even if that room has become unavailable since.

    Raises
    ------
    BookingRoomUnavailableException
        If the room does not exist, belongs to another organization, or is
        newly chosen but not available.
    """
    room = get_active_room_by_guid(session=session, guid=room_guid)
    if room is None or room.organization_id != organization_id:
        raise BookingRoomUnavailableException(message="The selected room can't be booked.")
    if room.id != current_room_id and room.status != RoomStatus.AVAILABLE:
        raise BookingRoomUnavailableException(
            message=f"Room {room.room_number} is {_ROOM_STATUS_LABELS[room.status]} and can't be booked."
        )
    return room


def _ensure_room_is_free(
    *,
    session: Session,
    room: Room,
    check_in_date: date,
    check_out_date: date,
    exclude_booking_id: int | None,
) -> None:
    """Make sure no other active booking overlaps the stay.

    Call inside `room_booking_lock` so the answer stays true until the save.

    Raises
    ------
    BookingRoomUnavailableException
        If another confirmed or checked-in booking holds the room for part of the stay.
    """
    if has_overlapping_booking(
        session=session,
        room_id=room.id,  # type: ignore[arg-type]
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        exclude_booking_id=exclude_booking_id,
    ):
        raise BookingRoomUnavailableException(
            message=f"Room {room.room_number} is already booked for part of these dates."
        )


def _build_guest_entries(payload: BookingStayInput) -> list[BookingGuestEntry]:
    """Turn the request's guests into the ordered list to save (primary guest first).

    Raises
    ------
    BookingPrimaryGuestRequiredException
        If the primary guest is missing or lacks a phone number or an ID proof.
    """
    primary = payload.primary_guest
    if primary is None:
        raise BookingPrimaryGuestRequiredException(message="Add the primary guest.")
    if primary.phone is None or not primary.has_id_proof:
        raise BookingPrimaryGuestRequiredException(
            message="The primary guest needs a phone number and an ID proof."
        )
    return [
        BookingGuestEntry(data=primary, is_primary=True),
        *(BookingGuestEntry(data=guest, is_primary=False) for guest in payload.secondary_guests),
    ]


def _apply_price(*, booking: Booking, room: Room, refresh_rate: bool) -> None:
    """Set the booking's nights and total; take a new rate from the room type when asked."""
    if refresh_rate:
        booking.cost_per_night = room.room_type.cost_per_night
        booking.currency_unit_id = room.room_type.currency_unit_id
    booking.nights = booking_rules.calculate_nights(booking.check_in_date, booking.check_out_date)
    booking.total_amount = booking_rules.calculate_total_amount(booking.nights, booking.cost_per_night)


def _get_actor_role(*, session: Session, actor: OrganizationScopedActor) -> UserType:
    """Return the acting user's role, recorded on the bookings they register.

    Raises
    ------
    UserNotFoundException
        If the acting user has no user replica.
    """
    user = get_user_replica_by_id(session=session, user_id=actor.user_id)
    if user is None:
        raise UserNotFoundException()
    return user.role


def _now() -> datetime:
    """Current UTC time, as stored in the transition timestamps."""
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Use cases
# ---------------------------------------------------------------------------


def create_booking(*, session: Session, actor: OrganizationScopedActor, payload: BookingCreateRequest) -> BookingDetailResponse:
    """Create a booking with its guests.

    The booking is confirmed, or, for a stay that has already ended and is
    recorded as completed, saved directly as checked out. The primary guest
    is emailed a confirmation for confirmed bookings.

    Parameters
    ----------
    session : Session
        Active database session.
    actor : OrganizationScopedActor
        The caller and, for owners and managers, their active organization.
    payload : BookingCreateRequest
        Validated booking fields and guests.

    Returns
    -------
    BookingDetailResponse
        The created booking.

    Raises
    ------
    BookingOrganizationRequiredException
        If an admin does not choose an organization.
    OrganizationNotFoundException
        If an admin chooses a missing or inactive organization.
    BookingInvalidDatesException
        If the stay dates break a rule.
    BookingRoomUnavailableException
        If the room can't be booked or is taken for part of the stay.
    BookingPrimaryGuestRequiredException
        If the primary guest is missing or incomplete.
    BookingGuestCapacityExceededException
        If the guests do not fit the room.
    """
    today = booking_rules.utc_today()
    organization_id = _resolve_organization_id(
        session=session,
        actor=actor,
        organization_guid=payload.organization_guid,
    )
    booking_rules.validate_stay_dates(
        check_in_date=payload.check_in_date,
        check_out_date=payload.check_out_date,
        today=today,
    )
    if payload.record_as_completed_stay:
        booking_rules.ensure_completed_stay_has_ended(check_out_date=payload.check_out_date, today=today)
    room = _get_bookable_room_or_raise(
        session=session,
        room_guid=payload.room_guid,
        organization_id=organization_id,
        current_room_id=None,
    )
    guests = _build_guest_entries(payload)
    booking_rules.ensure_guest_capacity(
        guest_count=len(guests),
        capacity=room.room_type.capacity,
        room_number=room.room_number,
    )
    nights = booking_rules.calculate_nights(payload.check_in_date, payload.check_out_date)
    booking = Booking(
        reference=booking_rules.format_booking_reference(
            _now().year, next_booking_reference_number(session=session)
        ),
        organization_id=organization_id,
        room_id=room.id,  # type: ignore[arg-type]
        booked_by=actor.user_id,
        booked_by_role=_get_actor_role(session=session, actor=actor),
        check_in_date=payload.check_in_date,
        check_out_date=payload.check_out_date,
        nights=nights,
        guest_count=len(guests),
        notes=payload.notes,
        cost_per_night=room.room_type.cost_per_night,
        total_amount=booking_rules.calculate_total_amount(nights, room.room_type.cost_per_night),
        currency_unit_id=room.room_type.currency_unit_id,
        created_by=actor.user_id,  # type: ignore[call-arg]
        updated_by=actor.user_id,  # type: ignore[call-arg]
    )
    if payload.record_as_completed_stay:
        completed_at = _now()
        booking.status = BookingStatus.CHECKED_OUT
        booking.checked_in_at = booking.checked_out_at = completed_at
        booking.checked_in_by = booking.checked_out_by = actor.user_id

    with room_booking_lock(session=session, room_id=room.id):  # type: ignore[arg-type]
        _ensure_room_is_free(
            session=session,
            room=room,
            check_in_date=payload.check_in_date,
            check_out_date=payload.check_out_date,
            exclude_booking_id=None,
        )
        add_booking(session=session, booking=booking)
        replace_booking_guests(session=session, booking=booking, guests=guests, actor_id=actor.user_id)
        booking = save_booking(session=session, booking=booking)

    if booking.status == BookingStatus.CONFIRMED:
        send_booking_confirmed_email(booking=booking, primary_guest=_primary_guest_of(session=session, booking=booking))
    return _to_detail_response(session=session, booking=booking)


def update_booking(*, session: Session, actor: OrganizationScopedActor, payload: BookingUpdateRequest) -> BookingDetailResponse:
    """Update the booking identified by `payload.guid` and its complete guest list.

    Confirmed bookings can change everything; checked-in bookings can change
    guests, notes and the check-out date. The primary guest is emailed when
    the room or dates change.

    Parameters
    ----------
    session : Session
        Active database session.
    actor : OrganizationScopedActor
        The caller and, for owners and managers, their active organization.
    payload : BookingUpdateRequest
        GUID of the booking, its new fields and every guest it should have.

    Returns
    -------
    BookingDetailResponse
        The updated booking.

    Raises
    ------
    BookingNotFoundException
        If the booking is missing or not visible to the actor.
    BookingNotEditableException
        If the booking's status does not allow the change.
    BookingInvalidDatesException
        If the stay dates break a rule.
    BookingRoomUnavailableException
        If a new room can't be booked or the room is taken for the new dates.
    BookingPrimaryGuestRequiredException
        If the primary guest is missing or incomplete.
    BookingGuestCapacityExceededException
        If the guests do not fit the room.
    """
    booking = _get_visible_booking_or_raise(session=session, actor=actor, guid=payload.guid)
    room = _get_bookable_room_or_raise(
        session=session,
        room_guid=payload.room_guid,
        organization_id=booking.organization_id,
        current_room_id=booking.room_id,
    )
    room_changed = room.id != booking.room_id
    check_in_changed = payload.check_in_date != booking.check_in_date
    dates_changed = check_in_changed or payload.check_out_date != booking.check_out_date
    booking_rules.ensure_update_allowed(
        status=booking.status,
        room_changed=room_changed,
        check_in_date_changed=check_in_changed,
    )
    booking_rules.validate_stay_dates(
        check_in_date=payload.check_in_date,
        check_out_date=payload.check_out_date,
        today=booking_rules.utc_today(),
    )
    guests = _build_guest_entries(payload)
    booking_rules.ensure_guest_capacity(
        guest_count=len(guests),
        capacity=room.room_type.capacity,
        room_number=room.room_number,
    )
    previous_stay = BookingStaySnapshot.of(booking)
    booking.room_id = room.id  # type: ignore[assignment]
    booking.room = room
    booking.check_in_date = payload.check_in_date
    booking.check_out_date = payload.check_out_date
    booking.guest_count = len(guests)
    booking.notes = payload.notes
    booking.updated_by = actor.user_id
    if room_changed or dates_changed:
        # A confirmed booking is priced again at today's rate; a checked-in
        # stay keeps its agreed rate for the changed nights.
        _apply_price(booking=booking, room=room, refresh_rate=booking.status == BookingStatus.CONFIRMED)

    with room_booking_lock(session=session, room_id=room.id):  # type: ignore[arg-type]
        if room_changed or dates_changed:
            _ensure_room_is_free(
                session=session,
                room=room,
                check_in_date=payload.check_in_date,
                check_out_date=payload.check_out_date,
                exclude_booking_id=booking.id,
            )
        replace_booking_guests(session=session, booking=booking, guests=guests, actor_id=actor.user_id)
        booking = save_booking(session=session, booking=booking)

    send_booking_updated_email(
        booking=booking,
        primary_guest=_primary_guest_of(session=session, booking=booking),
        previous=previous_stay,
    )
    return _to_detail_response(session=session, booking=booking)


def get_booking(*, session: Session, actor: OrganizationScopedActor, guid: UUID) -> BookingDetailResponse:
    """Return one booking the actor may manage, with its guests and history.

    Raises
    ------
    BookingNotFoundException
        If the booking is missing or not visible to the actor.
    """
    return _to_detail_response(session=session, booking=_get_visible_booking_or_raise(session=session, actor=actor, guid=guid))


def list_bookings(*, session: Session, actor: OrganizationScopedActor, query: BookingListQueryParams) -> BookingListResponse:
    """Return a paginated, searchable and filterable list of bookings.

    Admins get the bookings of every active organization; owners and managers
    get the bookings of their active organization.

    Parameters
    ----------
    session : Session
        Active database session.
    actor : OrganizationScopedActor
        The caller and, for owners and managers, their active organization.
    query : BookingListQueryParams
        Search, filters, sorting and pagination options.

    Returns
    -------
    BookingListResponse
        The requested page and the total matching count.
    """
    organization_id = None if actor.is_admin else get_member_active_organization_id(actor)
    bookings, total_count = list_bookings_page(session=session, query=query, organization_id=organization_id)
    primary_by_booking = {
        mapping.booking_id: mapping.guest
        for mapping in list_booking_guests(session=session, booking_ids=[b.id for b in bookings])  # type: ignore[misc]
        if mapping.is_primary
    }
    today = booking_rules.utc_today()
    return BookingListResponse(
        items=[_to_list_item(booking, primary_by_booking.get(booking.id), today) for booking in bookings],  # type: ignore[arg-type]
        total_count=total_count,
        page_number=query.page_number,
        page_size=query.page_size,
    )


def list_available_rooms(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    query: AvailableRoomsQueryParams,
) -> list[AvailableRoom]:
    """List the rooms that can be booked for a stay.

    Raises
    ------
    BookingOrganizationRequiredException
        If an admin does not choose an organization.
    BookingInvalidDatesException
        If the stay dates break a rule.
    BookingNotFoundException
        If `exclude_booking_guid` names a booking not visible to the actor.
    """
    exclude_booking_id = None
    if query.exclude_booking_guid is not None:
        excluded = _get_visible_booking_or_raise(session=session, actor=actor, guid=query.exclude_booking_guid)
        organization_id = excluded.organization_id
        exclude_booking_id = excluded.id
    else:
        organization_id = _resolve_organization_id(
            session=session,
            actor=actor,
            organization_guid=query.organization_guid,
        )
    booking_rules.validate_stay_dates(
        check_in_date=query.check_in_date,
        check_out_date=query.check_out_date,
        today=booking_rules.utc_today(),
    )
    rooms = list_available_rooms_repo(
        session=session,
        organization_id=organization_id,
        check_in_date=query.check_in_date,
        check_out_date=query.check_out_date,
        exclude_booking_id=exclude_booking_id,
    )
    return [
        AvailableRoom(
            guid=room.guid,  # type: ignore[arg-type]
            room_number=room.room_number,
            floor=room.floor,
            room_type=AvailableRoomTypeReference(
                guid=room.room_type.guid,  # type: ignore[arg-type]
                name=room.room_type.name,
                capacity=room.room_type.capacity,
                cost_per_night=room.room_type.cost_per_night,
            ),
            currency=CurrencyUnitOption.model_validate(room.room_type.currency_unit, from_attributes=True),
        )
        for room in rooms
    ]


def check_in_booking(*, session: Session, actor: OrganizationScopedActor, payload: BookingTransitionRequest) -> BookingDetailResponse:
    """Mark a confirmed booking's guests as arrived.

    Raises
    ------
    BookingNotFoundException
        If the booking is missing or not visible to the actor.
    BookingInvalidStatusTransitionException
        If the booking is not confirmed or its check-in date has not come.
    """
    booking = _get_visible_booking_or_raise(session=session, actor=actor, guid=payload.guid)
    booking_rules.ensure_can_check_in(
        status=booking.status,
        check_in_date=booking.check_in_date,
        today=booking_rules.utc_today(),
    )
    booking.status = BookingStatus.CHECKED_IN
    booking.checked_in_at = _now()
    booking.checked_in_by = actor.user_id
    booking.updated_by = actor.user_id
    return _to_detail_response(session=session, booking=save_booking(session=session, booking=booking))


def check_out_booking(*, session: Session, actor: OrganizationScopedActor, payload: BookingTransitionRequest) -> BookingDetailResponse:
    """Mark a checked-in booking's guests as departed.

    An early check-out moves the check-out date to today and prices the
    stay for the nights actually stayed.

    Raises
    ------
    BookingNotFoundException
        If the booking is missing or not visible to the actor.
    BookingInvalidStatusTransitionException
        If the booking is not checked in, or today is its check-in day.
    """
    booking = _get_visible_booking_or_raise(session=session, actor=actor, guid=payload.guid)
    booking_rules.ensure_can_check_out(status=booking.status)
    check_out_date = booking_rules.resolve_check_out_date(
        check_in_date=booking.check_in_date,
        check_out_date=booking.check_out_date,
        today=booking_rules.utc_today(),
    )
    if check_out_date != booking.check_out_date:
        booking.check_out_date = check_out_date
        _apply_price(booking=booking, room=booking.room, refresh_rate=False)
    booking.status = BookingStatus.CHECKED_OUT
    booking.checked_out_at = _now()
    booking.checked_out_by = actor.user_id
    booking.updated_by = actor.user_id
    return _to_detail_response(session=session, booking=save_booking(session=session, booking=booking))


def cancel_booking(*, session: Session, actor: OrganizationScopedActor, payload: BookingCancelRequest) -> BookingDetailResponse:
    """Cancel a confirmed booking and email the primary guest.

    Raises
    ------
    BookingNotFoundException
        If the booking is missing or not visible to the actor.
    BookingInvalidStatusTransitionException
        If the booking is not confirmed.
    """
    booking = _get_visible_booking_or_raise(session=session, actor=actor, guid=payload.guid)
    booking_rules.ensure_can_cancel(status=booking.status)
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = _now()
    booking.cancelled_by = actor.user_id
    booking.cancellation_reason = payload.reason
    booking.updated_by = actor.user_id
    booking = save_booking(session=session, booking=booking)
    send_booking_cancelled_email(booking=booking, primary_guest=_primary_guest_of(session=session, booking=booking))
    return _to_detail_response(session=session, booking=booking)


def get_today_summary(
    *,
    session: Session,
    actor: OrganizationScopedActor,
    query: BookingTodayQueryParams,
) -> BookingTodaySummaryResponse:
    """Count the active organization's arrivals, departures and in-house bookings on a day."""
    arrivals, departures, in_house = count_today(
        session=session,
        organization_id=get_member_active_organization_id(actor),
        on_date=query.on_date or booking_rules.utc_today(),
    )
    return BookingTodaySummaryResponse(arrivals=arrivals, departures=departures, in_house=in_house)


def get_room_occupancies(*, session: Session, organization_id: int, on_date: date) -> dict[int, RoomOccupancy]:
    """Return, per room, the booking that occupies it on a date (for the floor chart).

    Parameters
    ----------
    session : Session
        Active database session.
    organization_id : int
        Internal ID of the organization.
    on_date : date
        The day to look at.

    Returns
    -------
    dict[int, RoomOccupancy]
        Occupancy keyed by the room's internal ID; free rooms are absent.
    """
    bookings_by_room: dict[int, list[Booking]] = defaultdict(list)
    for booking in list_bookings_around_date(session=session, organization_id=organization_id, on_date=on_date):
        bookings_by_room[booking.room_id].append(booking)

    occupancies = {
        room_id: occupancy
        for room_id, bookings in bookings_by_room.items()
        if (occupancy := booking_rules.find_occupancy(bookings, on_date)) is not None
    }
    primary_names = {
        mapping.booking_id: f"{mapping.guest.first_name} {mapping.guest.last_name}"
        for mapping in list_booking_guests(
            session=session,
            booking_ids=[occupancy.booking.id for occupancy in occupancies.values()],  # type: ignore[misc]
        )
        if mapping.is_primary
    }
    return {
        room_id: RoomOccupancy(
            booking_guid=occupancy.booking.guid,  # type: ignore[arg-type]
            reference=occupancy.booking.reference,
            status=occupancy.booking.status,
            primary_guest_name=primary_names.get(occupancy.booking.id),  # type: ignore[arg-type]
            check_in_date=occupancy.booking.check_in_date,
            check_out_date=occupancy.booking.check_out_date,
            is_arriving=occupancy.is_arriving,
            is_departing=occupancy.is_departing,
        )
        for room_id, occupancy in occupancies.items()
    }


def ensure_room_has_no_active_bookings(*, session: Session, room: Room) -> None:
    """Refuse to remove a room that still has confirmed or checked-in bookings.

    Raises
    ------
    RoomHasActiveBookingsException
        If the room has such a booking.
    """
    if has_active_bookings_for_room(session=session, room_id=room.id):  # type: ignore[arg-type]
        raise RoomHasActiveBookingsException(
            message=f"Room {room.room_number} has active bookings and can't be deleted."
        )
