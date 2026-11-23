"""Unit tests for the pure booking rules (no database needed)."""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

import pytest

from booking.api.services import booking_rules
from booking.exceptions.definitions.validation_exceptions import (
    BookingGuestCapacityExceededException,
    BookingInvalidDatesException,
    BookingInvalidStatusTransitionException,
    BookingNotEditableException,
)
from booking.types.enums import BookingAction, BookingStatus

TODAY = date(2026, 11, 23)


@dataclass
class Stay:
    """Minimal booking stand-in for the occupancy rules."""

    status: BookingStatus
    check_in_date: date
    check_out_date: date


def days(offset: int) -> date:
    return TODAY + timedelta(days=offset)


class TestReferenceAndPrice:
    def test_reference_is_zero_padded(self) -> None:
        assert booking_rules.format_booking_reference(2026, 123) == "BK-2026-000123"

    def test_nights_and_total(self) -> None:
        nights = booking_rules.calculate_nights(days(0), days(3))
        assert nights == 3
        assert booking_rules.calculate_total_amount(nights, Decimal("2500.00")) == Decimal("7500.00")

    def test_total_is_rounded_to_cents(self) -> None:
        assert booking_rules.calculate_total_amount(3, Decimal("33.335")) == Decimal("100.01")


class TestStayDates:
    def test_valid_and_back_dated_stays_pass(self) -> None:
        booking_rules.validate_stay_dates(check_in_date=days(1), check_out_date=days(4), today=TODAY)
        booking_rules.validate_stay_dates(check_in_date=days(-10), check_out_date=days(-7), today=TODAY)

    @pytest.mark.parametrize(
        ("check_in", "check_out", "message"),
        [
            (0, 0, "Check-out must be after check-in."),
            (3, 1, "Check-out must be after check-in."),
            (0, 91, "A booking can be at most 90 nights."),
            (731, 732, "Check-in can be at most 2 years ahead."),
        ],
    )
    def test_invalid_stays_are_refused(self, check_in: int, check_out: int, message: str) -> None:
        with pytest.raises(BookingInvalidDatesException) as error:
            booking_rules.validate_stay_dates(check_in_date=days(check_in), check_out_date=days(check_out), today=TODAY)
        assert error.value.message == message

    def test_ninety_nights_and_two_years_ahead_are_allowed(self) -> None:
        booking_rules.validate_stay_dates(check_in_date=days(0), check_out_date=days(90), today=TODAY)
        booking_rules.validate_stay_dates(check_in_date=days(730), check_out_date=days(731), today=TODAY)

    def test_completed_stay_must_have_ended(self) -> None:
        booking_rules.ensure_completed_stay_has_ended(check_out_date=TODAY, today=TODAY)
        with pytest.raises(BookingInvalidDatesException):
            booking_rules.ensure_completed_stay_has_ended(check_out_date=days(1), today=TODAY)


class TestCapacity:
    def test_guests_up_to_capacity_fit(self) -> None:
        booking_rules.ensure_guest_capacity(guest_count=2, capacity=2, room_number="201")

    def test_extra_guests_are_refused_with_a_helpful_message(self) -> None:
        with pytest.raises(BookingGuestCapacityExceededException) as error:
            booking_rules.ensure_guest_capacity(guest_count=3, capacity=2, room_number="201")
        assert error.value.message == "Room 201 fits 2 guests. Remove 1 guest or choose a larger room."


class TestMasking:
    @pytest.mark.parametrize(
        ("number", "masked"),
        [("123412341234", "••••••••1234"), ("1234", "1234"), ("12", "12"), (None, None)],
    )
    def test_only_the_last_four_characters_stay_visible(self, number: str | None, masked: str | None) -> None:
        assert booking_rules.mask_id_proof_number(number) == masked


class TestTransitions:
    def test_check_in_from_the_check_in_date_with_one_day_time_zone_tolerance(self) -> None:
        assert booking_rules.can_check_in(status=BookingStatus.CONFIRMED, check_in_date=TODAY, today=TODAY)
        assert booking_rules.can_check_in(status=BookingStatus.CONFIRMED, check_in_date=days(1), today=TODAY)
        assert not booking_rules.can_check_in(status=BookingStatus.CONFIRMED, check_in_date=days(2), today=TODAY)
        with pytest.raises(BookingInvalidStatusTransitionException):
            booking_rules.ensure_can_check_in(status=BookingStatus.CONFIRMED, check_in_date=days(2), today=TODAY)

    @pytest.mark.parametrize("status", [BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT, BookingStatus.CANCELLED])
    def test_only_confirmed_bookings_check_in_or_cancel(self, status: BookingStatus) -> None:
        with pytest.raises(BookingInvalidStatusTransitionException):
            booking_rules.ensure_can_check_in(status=status, check_in_date=TODAY, today=TODAY)
        with pytest.raises(BookingInvalidStatusTransitionException):
            booking_rules.ensure_can_cancel(status=status)

    def test_only_checked_in_bookings_check_out(self) -> None:
        booking_rules.ensure_can_check_out(status=BookingStatus.CHECKED_IN)
        with pytest.raises(BookingInvalidStatusTransitionException):
            booking_rules.ensure_can_check_out(status=BookingStatus.CONFIRMED)

    def test_early_check_out_moves_the_date_to_today(self) -> None:
        assert booking_rules.resolve_check_out_date(check_in_date=days(-2), check_out_date=days(3), today=TODAY) == TODAY

    def test_late_check_out_keeps_the_planned_date(self) -> None:
        assert booking_rules.resolve_check_out_date(check_in_date=days(-5), check_out_date=days(-1), today=TODAY) == days(-1)

    def test_check_out_on_the_check_in_day_is_refused(self) -> None:
        with pytest.raises(BookingInvalidStatusTransitionException):
            booking_rules.resolve_check_out_date(check_in_date=TODAY, check_out_date=days(2), today=TODAY)


class TestEditing:
    def test_confirmed_booking_can_change_everything(self) -> None:
        booking_rules.ensure_update_allowed(status=BookingStatus.CONFIRMED, room_changed=True, check_in_date_changed=True)

    def test_checked_in_booking_keeps_room_and_check_in_date(self) -> None:
        booking_rules.ensure_update_allowed(status=BookingStatus.CHECKED_IN, room_changed=False, check_in_date_changed=False)
        for room_changed, check_in_changed in [(True, False), (False, True)]:
            with pytest.raises(BookingNotEditableException):
                booking_rules.ensure_update_allowed(
                    status=BookingStatus.CHECKED_IN,
                    room_changed=room_changed,
                    check_in_date_changed=check_in_changed,
                )

    @pytest.mark.parametrize("status", [BookingStatus.CHECKED_OUT, BookingStatus.CANCELLED])
    def test_finished_bookings_are_read_only(self, status: BookingStatus) -> None:
        with pytest.raises(BookingNotEditableException):
            booking_rules.ensure_update_allowed(status=status, room_changed=False, check_in_date_changed=False)


class TestAllowedActions:
    @pytest.mark.parametrize(
        ("status", "check_in", "expected"),
        [
            (BookingStatus.CONFIRMED, 5, [BookingAction.EDIT, BookingAction.CANCEL]),
            (BookingStatus.CONFIRMED, 0, [BookingAction.EDIT, BookingAction.CHECK_IN, BookingAction.CANCEL]),
            (BookingStatus.CHECKED_IN, 0, [BookingAction.EDIT]),
            (BookingStatus.CHECKED_IN, -1, [BookingAction.EDIT, BookingAction.CHECK_OUT]),
            (BookingStatus.CHECKED_OUT, -3, []),
            (BookingStatus.CANCELLED, 2, []),
        ],
    )
    def test_actions_follow_status_and_dates(
        self, status: BookingStatus, check_in: int, expected: list[BookingAction]
    ) -> None:
        assert booking_rules.allowed_actions(status=status, check_in_date=days(check_in), today=TODAY) == expected


class TestOccupancy:
    def test_confirmed_stay_occupies_its_nights_only(self) -> None:
        stay = Stay(BookingStatus.CONFIRMED, days(-1), days(1))
        assert booking_rules.is_occupying(stay, TODAY)
        assert not booking_rules.is_occupying(stay, days(1))

    def test_checked_in_stay_occupies_its_check_out_day(self) -> None:
        assert booking_rules.is_occupying(Stay(BookingStatus.CHECKED_IN, days(-2), TODAY), TODAY)

    @pytest.mark.parametrize("status", [BookingStatus.CHECKED_OUT, BookingStatus.CANCELLED])
    def test_finished_stays_never_occupy(self, status: BookingStatus) -> None:
        assert not booking_rules.is_occupying(Stay(status, days(-1), days(1)), TODAY)

    def test_free_room(self) -> None:
        assert booking_rules.find_occupancy([Stay(BookingStatus.CONFIRMED, days(2), days(3))], TODAY) is None

    def test_arrival(self) -> None:
        arriving = Stay(BookingStatus.CONFIRMED, TODAY, days(2))
        occupancy = booking_rules.find_occupancy([arriving], TODAY)
        assert occupancy is not None
        assert occupancy.booking is arriving and occupancy.is_arriving and not occupancy.is_departing

    def test_turnover_day_shows_the_departing_stay_flagged_arriving(self) -> None:
        departing = Stay(BookingStatus.CHECKED_IN, days(-2), TODAY)
        arriving = Stay(BookingStatus.CONFIRMED, TODAY, days(3))
        occupancy = booking_rules.find_occupancy([arriving, departing], TODAY)
        assert occupancy is not None
        assert occupancy.booking is departing and occupancy.is_arriving and occupancy.is_departing

    def test_in_house_mid_stay(self) -> None:
        in_house = Stay(BookingStatus.CHECKED_IN, days(-2), days(2))
        occupancy = booking_rules.find_occupancy([in_house], TODAY)
        assert occupancy is not None
        assert occupancy.booking is in_house and not occupancy.is_arriving and not occupancy.is_departing
