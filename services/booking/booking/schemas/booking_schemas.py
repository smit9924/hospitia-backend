from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import (
    BeforeValidator,
    EmailStr,
    Field,
    StringConstraints,
    model_validator,
)

from booking.database.models.booking import (
    BOOKING_CANCELLATION_REASON_MAX_LENGTH,
    BOOKING_NOTES_MAX_LENGTH,
)
from booking.database.models.guest_detail import (
    GUEST_ADDRESS_MAX_LENGTH,
    GUEST_EMAIL_MAX_LENGTH,
    GUEST_ID_PROOF_NUMBER_MAX_LENGTH,
    GUEST_ID_PROOF_NUMBER_PATTERN,
    GUEST_MAX_AGE_YEARS,
    GUEST_NAME_MAX_LENGTH,
    GUEST_NATIONALITY_MAX_LENGTH,
    GUEST_PHONE_MAX_LENGTH,
    GUEST_PHONE_MIN_LENGTH,
    GUEST_PHONE_PATTERN,
)
from booking.database.models.room_type import ROOM_TYPE_MAX_CAPACITY
from booking.types.enums import (
    BookingAction,
    BookingStatus,
    Gender,
    IdProofType,
    UserType,
)
from booking.utils.text_utils import blank_text_to_none, strip_text

from .base_schemas import BaseSchema
from .currency_unit_schemas import CurrencyUnitOption
from .organization_schemas import OrganizationReference


def _optional_text(max_length: int) -> object:
    """Build an optional free-text type: trimmed, at most `max_length` characters, blank stored as null."""
    return Annotated[
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=max_length)] | None,
        BeforeValidator(blank_text_to_none),
    ]


_BookingNotes = _optional_text(BOOKING_NOTES_MAX_LENGTH)
_CancellationReason = _optional_text(BOOKING_CANCELLATION_REASON_MAX_LENGTH)
_GuestAddress = _optional_text(GUEST_ADDRESS_MAX_LENGTH)
_GuestNationality = _optional_text(GUEST_NATIONALITY_MAX_LENGTH)

_GuestName = Annotated[
    str,
    BeforeValidator(strip_text),
    StringConstraints(min_length=1, max_length=GUEST_NAME_MAX_LENGTH),
]


class BookingGuestInput(BaseSchema):
    """
    One guest of a booking, as entered in the guest popup.

    `guid` identifies an existing guest of the booking being updated, so it
    keeps its identity; leave it out for a new guest. Phone and ID proof are
    optional here; the primary guest must have both (checked by the
    service). ID proof type and number are given together or not at all.
    """

    guid: UUID | None = None
    first_name: _GuestName
    last_name: _GuestName
    gender: Gender
    date_of_birth: date
    phone: Annotated[
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True,
                min_length=GUEST_PHONE_MIN_LENGTH,
                max_length=GUEST_PHONE_MAX_LENGTH,
                pattern=GUEST_PHONE_PATTERN,
            ),
        ]
        | None,
        BeforeValidator(blank_text_to_none),
    ] = None
    email: Annotated[
        Annotated[EmailStr, StringConstraints(max_length=GUEST_EMAIL_MAX_LENGTH)] | None,
        BeforeValidator(blank_text_to_none),
    ] = None
    id_proof_type: IdProofType | None = None
    id_proof_number: Annotated[
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True,
                min_length=1,
                max_length=GUEST_ID_PROOF_NUMBER_MAX_LENGTH,
                pattern=GUEST_ID_PROOF_NUMBER_PATTERN,
            ),
        ]
        | None,
        BeforeValidator(blank_text_to_none),
    ] = None
    address: _GuestAddress = None  # type: ignore[valid-type]
    nationality: _GuestNationality = None  # type: ignore[valid-type]

    @model_validator(mode="after")
    def check_guest(self) -> Self:
        """Check the date of birth and that ID proof type and number come together."""
        today = date.today()
        oldest_birth_date = today - timedelta(days=round(GUEST_MAX_AGE_YEARS * 365.25))
        if not oldest_birth_date <= self.date_of_birth <= today:
            raise ValueError("Enter a valid date of birth.")
        if (self.id_proof_type is None) != (self.id_proof_number is None):
            raise ValueError("Enter both the ID proof type and number, or neither.")
        return self

    @property
    def has_id_proof(self) -> bool:
        """Whether both ID proof fields are filled in."""
        return self.id_proof_type is not None and self.id_proof_number is not None


class BookingStayInput(BaseSchema):
    """
    Booking fields shared by the create and update requests.

    `primary_guest` is optional here so a missing primary guest gets the
    booking's own error (`BookingPrimaryGuestRequiredException`).
    """

    room_guid: UUID
    check_in_date: date
    check_out_date: date
    notes: _BookingNotes = None  # type: ignore[valid-type]
    primary_guest: BookingGuestInput | None = None
    secondary_guests: list[BookingGuestInput] = Field(default_factory=list, max_length=ROOM_TYPE_MAX_CAPACITY - 1)

    @property
    def guest_count(self) -> int:
        """Number of guests in the request (primary + secondary)."""
        return (1 if self.primary_guest is not None else 0) + len(self.secondary_guests)


class BookingCreateRequest(BookingStayInput):
    """
    Request payload for creating a booking.

    `organization_guid` is read only for admins, who must choose the
    organization; owners and managers book in their active organization.
    `record_as_completed_stay` saves a stay that has already ended directly
    as checked out (back-dated entries).
    """

    organization_guid: UUID | None = None
    record_as_completed_stay: bool = False


class BookingUpdateRequest(BookingStayInput):
    """
    Request payload for updating the booking identified by `guid`.

    The guest lists are complete: guests of the booking left out are
    removed. A booking never moves to another organization.
    """

    guid: UUID


class BookingTransitionRequest(BaseSchema):
    """Request payload for checking in or checking out the booking identified by `guid`."""

    guid: UUID


class BookingCancelRequest(BaseSchema):
    """Request payload for cancelling the booking identified by `guid`, with an optional reason."""

    guid: UUID
    reason: _CancellationReason = None  # type: ignore[valid-type]


class UserReference(BaseSchema):
    """Minimal public reference to a user (e.g. who booked or checked in)."""

    guid: UUID
    first_name: str | None
    last_name: str | None


class BookingRoomTypeReference(BaseSchema):
    """The booked room's type and the number of guests it fits."""

    guid: UUID
    name: str
    capacity: int


class BookingRoomReference(BaseSchema):
    """The booked room."""

    guid: UUID
    room_number: str
    floor: int
    room_type: BookingRoomTypeReference


class BookingGuestResponse(BaseSchema):
    """
    A guest of a booking. `id_proof_number` is masked (e.g. "••••1234") in
    listings and shown in full in the booking details.
    """

    guid: UUID
    first_name: str
    last_name: str
    gender: Gender
    date_of_birth: date
    phone: str | None
    email: str | None
    id_proof_type: IdProofType | None
    id_proof_number: str | None
    address: str | None
    nationality: str | None


class BookingPrimaryGuestSummary(BaseSchema):
    """The primary guest as shown in the booking listing (ID number masked)."""

    guid: UUID
    first_name: str
    last_name: str
    phone: str | None
    id_proof_type: IdProofType | None
    id_proof_number: str | None


class BookingSummaryBase(BaseSchema):
    """Fields shared by the booking listing item and the booking details."""

    guid: UUID
    reference: str
    status: BookingStatus
    organization: OrganizationReference
    room: BookingRoomReference
    check_in_date: date
    check_out_date: date
    nights: int
    guest_count: int
    cost_per_night: Decimal
    total_amount: Decimal
    currency: CurrencyUnitOption
    booked_by: UserReference
    booked_by_role: UserType
    created_at: datetime
    allowed_actions: list[BookingAction]


class BookingListItem(BookingSummaryBase):
    """A booking row of the listing."""

    primary_guest: BookingPrimaryGuestSummary | None


class BookingDetailResponse(BookingSummaryBase):
    """A booking with its guests (ID numbers in full) and its status history."""

    notes: str | None
    updated_at: datetime
    checked_in_at: datetime | None
    checked_in_by: UserReference | None
    checked_out_at: datetime | None
    checked_out_by: UserReference | None
    cancelled_at: datetime | None
    cancelled_by: UserReference | None
    cancellation_reason: str | None
    primary_guest: BookingGuestResponse | None
    secondary_guests: list[BookingGuestResponse]


class BookingListQueryParams(BaseSchema):
    """
    Query parameters for the paginated booking listing endpoint.

    `search_term` matches the booking reference, the primary guest's name or
    phone, or the room number. `statuses` keeps bookings with any of the
    given statuses. `from_date`/`to_date` keep bookings whose stay overlaps
    that range (both inclusive).
    """

    search_term: str | None = None
    statuses: list[BookingStatus] = Field(default_factory=list)
    from_date: date | None = None
    to_date: date | None = None
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: Literal["checkInDate", "createdAt"] = "checkInDate"
    sort_direction: Literal["asc", "desc"] = "desc"
    page_number: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def check_date_range(self) -> Self:
        """Make sure the range does not end before it starts."""
        if self.from_date and self.to_date and self.to_date < self.from_date:
            raise ValueError("The end date must not be before the start date.")
        return self


class BookingListResponse(BaseSchema):
    items: list[BookingListItem]
    total_count: int
    page_number: int
    page_size: int


class AvailableRoomsQueryParams(BaseSchema):
    """
    Query parameters for listing the rooms free for a stay.

    `organization_guid` is read only for admins; owners and managers get
    their active organization's rooms. `exclude_booking_guid` ignores the
    booking being edited, so it does not block its own room.
    """

    organization_guid: UUID | None = None
    check_in_date: date
    check_out_date: date
    exclude_booking_guid: UUID | None = None


class AvailableRoomTypeReference(BookingRoomTypeReference):
    """Room type of a free room, with the nightly cost used to price the stay."""

    cost_per_night: Decimal


class AvailableRoom(BaseSchema):
    """A room that can be booked for the requested stay."""

    guid: UUID
    room_number: str
    floor: int
    room_type: AvailableRoomTypeReference
    currency: CurrencyUnitOption


class BookingTodayQueryParams(BaseSchema):
    """`on_date` is the caller's local date; it defaults to the server's (UTC) date."""

    on_date: date | None = None


class BookingTodaySummaryResponse(BaseSchema):
    """
    Today's activity of the active organization.

    `arrivals`: confirmed bookings checking in today; `departures`:
    checked-in bookings checking out today; `in_house`: checked-in bookings.
    """

    arrivals: int
    departures: int
    in_house: int


class RoomOccupancy(BaseSchema):
    """The booking holding a room on the dashboard's date."""

    booking_guid: UUID
    reference: str
    status: BookingStatus
    primary_guest_name: str | None
    check_in_date: date
    check_out_date: date
    is_arriving: bool
    is_departing: bool
