"""
Pure booking rules: stay dates, price, capacity, status transitions,
masking and occupancy.

Nothing here touches the database, so every rule can be unit-tested on its
own; `booking_service` combines these rules with the repositories.

A stay covers the nights from the check-in date up to, not including, the
check-out date, so one guest can leave and the next arrive on the same day.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol

from booking.database.models.booking import BOOKING_MAX_NIGHTS, BOOKING_MIN_NIGHTS
from booking.exceptions.definitions.validation_exceptions import (
    BookingGuestCapacityExceededException,
    BookingInvalidDatesException,
    BookingInvalidStatusTransitionException,
    BookingNotEditableException,
)
from booking.types.enums import BookingAction, BookingStatus

# How far ahead a stay may start.
BOOKING_MAX_DAYS_AHEAD = 730

# Server dates are UTC while users enter local dates; checking in is allowed
# from one day before the check-in date so time zones ahead of UTC are not
# refused on their check-in morning.
CHECK_IN_TIME_ZONE_TOLERANCE = timedelta(days=1)

# Bookings that hold their room for their dates.
ACTIVE_BOOKING_STATUSES: tuple[BookingStatus, ...] = (BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN)

# Characters of an ID proof number left visible when masked.
ID_PROOF_VISIBLE_CHARACTERS = 4
MASK_CHARACTER = "•"

_CENT = Decimal("0.01")


class StayLike(Protocol):
    """The booking attributes the occupancy rules read."""

    status: BookingStatus
    check_in_date: date
    check_out_date: date


@dataclass(frozen=True)
class Occupancy[T: StayLike]:
    """
    The booking that occupies a room on a date.

    Attributes
    ----------
    booking : T
        The occupying booking.
    is_arriving : bool
        A confirmed booking checks in on the date.
    is_departing : bool
        A checked-in booking checks out on the date.
    """

    booking: T
    is_arriving: bool
    is_departing: bool


def utc_today() -> date:
    """Return today's date in UTC, the server's reference date."""
    return datetime.now(UTC).date()


def format_booking_reference(year: int, number: int) -> str:
    """Format a booking reference such as "BK-2026-000123".

    Parameters
    ----------
    year : int
        Creation year.
    number : int
        Globally increasing booking number.

    Returns
    -------
    str
        The reference, with the number zero-padded to six digits.
    """
    return f"BK-{year}-{number:06d}"


def calculate_nights(check_in_date: date, check_out_date: date) -> int:
    """Return the number of nights between check-in and check-out."""
    return (check_out_date - check_in_date).days


def calculate_total_amount(nights: int, cost_per_night: Decimal) -> Decimal:
    """Return `nights * cost_per_night`, rounded to two decimal places."""
    return (cost_per_night * nights).quantize(_CENT, rounding=ROUND_HALF_UP)


def validate_stay_dates(*, check_in_date: date, check_out_date: date, today: date) -> None:
    """Check the stay dates of a booking.

    Back-dated stays are allowed; a stay must last 1 to 90 nights and start
    at most two years after `today`.

    Parameters
    ----------
    check_in_date, check_out_date : date
        Requested stay dates.
    today : date
        Reference date.

    Raises
    ------
    BookingInvalidDatesException
        If any rule is broken; the message names the rule.
    """
    nights = calculate_nights(check_in_date, check_out_date)
    if nights < BOOKING_MIN_NIGHTS:
        raise BookingInvalidDatesException(message="Check-out must be after check-in.")
    if nights > BOOKING_MAX_NIGHTS:
        raise BookingInvalidDatesException(message=f"A booking can be at most {BOOKING_MAX_NIGHTS} nights.")
    if check_in_date > today + timedelta(days=BOOKING_MAX_DAYS_AHEAD):
        raise BookingInvalidDatesException(message="Check-in can be at most 2 years ahead.")


def ensure_completed_stay_has_ended(*, check_out_date: date, today: date) -> None:
    """Make sure a stay recorded as completed has already ended.

    Raises
    ------
    BookingInvalidDatesException
        If the check-out date is after `today`.
    """
    if check_out_date > today:
        raise BookingInvalidDatesException(
            message="Only a stay whose check-out date has passed can be recorded as completed."
        )


def ensure_guest_capacity(*, guest_count: int, capacity: int, room_number: str) -> None:
    """Make sure the guests fit the room.

    Parameters
    ----------
    guest_count : int
        Primary + secondary guests.
    capacity : int
        Maximum number of guests of the room's type.
    room_number : str
        Room number, used in the message.

    Raises
    ------
    BookingGuestCapacityExceededException
        If there are more guests than the room fits.
    """
    if guest_count > capacity:
        extra = guest_count - capacity
        noun = "guest" if extra == 1 else "guests"
        raise BookingGuestCapacityExceededException(
            message=f"Room {room_number} fits {capacity} guests. Remove {extra} {noun} or choose a larger room."
        )


def mask_id_proof_number(id_proof_number: str | None) -> str | None:
    """Mask all but the last four characters of an ID proof number.

    Parameters
    ----------
    id_proof_number : str | None
        Full number, if any.

    Returns
    -------
    str | None
        For example "••••••••1234", or ``None`` when there is no number.
    """
    if id_proof_number is None:
        return None
    hidden = max(len(id_proof_number) - ID_PROOF_VISIBLE_CHARACTERS, 0)
    return MASK_CHARACTER * hidden + id_proof_number[hidden:]


def can_check_in(*, status: BookingStatus, check_in_date: date, today: date) -> bool:
    """Whether a booking can be checked in on `today` (see `CHECK_IN_TIME_ZONE_TOLERANCE`)."""
    return status == BookingStatus.CONFIRMED and today >= check_in_date - CHECK_IN_TIME_ZONE_TOLERANCE


def can_check_out(*, status: BookingStatus, check_in_date: date, today: date) -> bool:
    """Whether a booking can be checked out on `today`; at least one night must have passed."""
    return status == BookingStatus.CHECKED_IN and today > check_in_date


def resolve_check_out_date(*, check_in_date: date, check_out_date: date, today: date) -> date:
    """Return the check-out date to store when guests check out on `today`.

    An early check-out moves the check-out date to `today`; checking out on
    or after the planned date keeps the planned date.

    Raises
    ------
    BookingInvalidStatusTransitionException
        If `today` is the check-in day or earlier (a stay is at least one night).
    """
    if today <= check_in_date:
        raise BookingInvalidStatusTransitionException(
            message="Guests can check out from the day after check-in."
        )
    return min(check_out_date, today)


def ensure_can_check_in(*, status: BookingStatus, check_in_date: date, today: date) -> None:
    """Raise unless the booking can be checked in on `today`.

    Raises
    ------
    BookingInvalidStatusTransitionException
        If the booking is not confirmed or its check-in date has not come.
    """
    if status != BookingStatus.CONFIRMED:
        raise BookingInvalidStatusTransitionException(message="Only a confirmed booking can be checked in.")
    if not can_check_in(status=status, check_in_date=check_in_date, today=today):
        raise BookingInvalidStatusTransitionException(message="Guests can check in from the check-in date.")


def ensure_can_check_out(*, status: BookingStatus) -> None:
    """Raise unless the booking is checked in.

    Raises
    ------
    BookingInvalidStatusTransitionException
        If the booking is not checked in.
    """
    if status != BookingStatus.CHECKED_IN:
        raise BookingInvalidStatusTransitionException(message="Only a checked-in booking can be checked out.")


def ensure_can_cancel(*, status: BookingStatus) -> None:
    """Raise unless the booking is confirmed.

    Raises
    ------
    BookingInvalidStatusTransitionException
        If the booking is checked in, checked out or already cancelled.
    """
    if status != BookingStatus.CONFIRMED:
        raise BookingInvalidStatusTransitionException(message="Only a confirmed booking can be cancelled.")


def ensure_update_allowed(
    *,
    status: BookingStatus,
    room_changed: bool,
    check_in_date_changed: bool,
) -> None:
    """Check that an update only changes what the booking's status allows.

    Confirmed bookings can change everything; checked-in bookings can change
    guests, notes and the check-out date; finished bookings are read-only.

    Raises
    ------
    BookingNotEditableException
        If the booking is checked out or cancelled, or a checked-in booking's
        room or check-in date would change.
    """
    if status in (BookingStatus.CHECKED_OUT, BookingStatus.CANCELLED):
        raise BookingNotEditableException(message="A checked-out or cancelled booking can't be changed.")
    if status == BookingStatus.CHECKED_IN and (room_changed or check_in_date_changed):
        raise BookingNotEditableException(
            message="The room and check-in date of a checked-in booking can't be changed."
        )


def allowed_actions(*, status: BookingStatus, check_in_date: date, today: date) -> list[BookingAction]:
    """Return the actions the booking's status and dates allow on `today`.

    Parameters
    ----------
    status : BookingStatus
        Current status.
    check_in_date : date
        Check-in date.
    today : date
        Reference date.

    Returns
    -------
    list[BookingAction]
        In display order: edit, check in, check out, cancel.
    """
    actions: list[BookingAction] = []
    if status in ACTIVE_BOOKING_STATUSES:
        actions.append(BookingAction.EDIT)
    if can_check_in(status=status, check_in_date=check_in_date, today=today):
        actions.append(BookingAction.CHECK_IN)
    if can_check_out(status=status, check_in_date=check_in_date, today=today):
        actions.append(BookingAction.CHECK_OUT)
    if status == BookingStatus.CONFIRMED:
        actions.append(BookingAction.CANCEL)
    return actions


def is_occupying(booking: StayLike, on_date: date) -> bool:
    """Whether the booking holds its room on `on_date`.

    A confirmed or checked-in booking occupies its nights; a checked-in
    booking also occupies its check-out day until the guests leave.
    """
    if booking.status not in ACTIVE_BOOKING_STATUSES:
        return False
    if booking.check_in_date <= on_date < booking.check_out_date:
        return True
    return booking.status == BookingStatus.CHECKED_IN and booking.check_out_date == on_date


def find_occupancy[T: StayLike](bookings: Sequence[T], on_date: date) -> Occupancy[T] | None:
    """Pick the booking that occupies one room on `on_date`.

    On a turnover day the departing (checked-in) booking is shown and the
    occupancy is flagged as arriving too.

    Parameters
    ----------
    bookings : Sequence[T]
        Bookings of one room.
    on_date : date
        Date to look at.

    Returns
    -------
    Occupancy[T] | None
        The occupying booking, or ``None`` when the room is free.
    """
    occupying = [booking for booking in bookings if is_occupying(booking, on_date)]
    if not occupying:
        return None
    departing = next(
        (b for b in occupying if b.status == BookingStatus.CHECKED_IN and b.check_out_date == on_date),
        None,
    )
    arriving = next(
        (b for b in occupying if b.status == BookingStatus.CONFIRMED and b.check_in_date == on_date),
        None,
    )
    shown = departing or arriving or occupying[0]
    return Occupancy(booking=shown, is_arriving=arriving is not None, is_departing=departing is not None)


__all__ = [
    "ACTIVE_BOOKING_STATUSES",
    "BOOKING_MAX_DAYS_AHEAD",
    "Occupancy",
    "allowed_actions",
    "calculate_nights",
    "calculate_total_amount",
    "can_check_in",
    "can_check_out",
    "ensure_can_cancel",
    "ensure_can_check_in",
    "ensure_can_check_out",
    "ensure_completed_stay_has_ended",
    "ensure_guest_capacity",
    "ensure_update_allowed",
    "find_occupancy",
    "format_booking_reference",
    "is_occupying",
    "mask_id_proof_number",
    "resolve_check_out_date",
    "utc_today",
    "validate_stay_dates",
]
