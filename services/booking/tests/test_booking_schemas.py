"""Unit tests for booking request validation."""

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from booking.schemas.booking_schemas import (
    BookingCreateRequest,
    BookingGuestInput,
    BookingListQueryParams,
)


def guest(**overrides: object) -> dict[str, object]:
    return {"firstName": "Asha", "lastName": "Rao", "gender": "female", "dateOfBirth": "1990-05-17"} | overrides


class TestGuestInput:
    def test_text_is_trimmed_and_blank_optional_text_is_null(self) -> None:
        data = BookingGuestInput.model_validate(guest(firstName="  Asha ", phone="  ", address=" ", nationality=""))
        assert data.first_name == "Asha"
        assert data.phone is None and data.address is None and data.nationality is None

    def test_id_proof_type_and_number_come_together(self) -> None:
        assert BookingGuestInput.model_validate(guest(idProofType="passport", idProofNumber="P-1234567")).has_id_proof
        with pytest.raises(ValidationError, match="both the ID proof type and number"):
            BookingGuestInput.model_validate(guest(idProofType="passport"))
        with pytest.raises(ValidationError, match="both the ID proof type and number"):
            BookingGuestInput.model_validate(guest(idProofNumber="123"))

    @pytest.mark.parametrize("birth_date", [date.today() + timedelta(days=1), date(1890, 1, 1)])
    def test_date_of_birth_must_be_plausible(self, birth_date: date) -> None:
        with pytest.raises(ValidationError, match="valid date of birth"):
            BookingGuestInput.model_validate(guest(dateOfBirth=birth_date.isoformat()))

    @pytest.mark.parametrize("phone", ["12345", "+91 98450 12345 0000000", "98450-ABC-12"])
    def test_invalid_phone_numbers_are_refused(self, phone: str) -> None:
        with pytest.raises(ValidationError):
            BookingGuestInput.model_validate(guest(phone=phone))

    def test_invalid_email_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            BookingGuestInput.model_validate(guest(email="not-an-email"))


class TestBookingRequests:
    def test_guest_count_includes_the_primary_guest(self) -> None:
        payload = BookingCreateRequest.model_validate(
            {
                "roomGuid": "00000000-0000-0000-0000-000000000001",
                "checkInDate": "2026-12-12",
                "checkOutDate": "2026-12-15",
                "primaryGuest": guest(),
                "secondaryGuests": [guest(firstName="Ravi")],
            }
        )
        assert payload.guest_count == 2
        assert payload.record_as_completed_stay is False

    def test_list_date_range_must_not_end_before_it_starts(self) -> None:
        with pytest.raises(ValidationError, match="end date"):
            BookingListQueryParams.model_validate({"fromDate": "2026-12-10", "toDate": "2026-12-01"})
