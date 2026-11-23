from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import AnyHttpUrl, EmailStr

from booking.schemas.base_schemas import BaseSchema
from booking.types.enums import UserType


class MqBaseSchema(BaseSchema):
    """
    Base schema for MQ messages.
    """
    pass


class MqForgotPasswordMessage(MqBaseSchema):
    """
    Schema for MQ forgot password messages.

    Attributes
    ----------
    to : list[str]
        List of recipient email addresses.
    subject : str
        Subject line of the email.
    user_first_name : str
        First name of the user.
    user_last_name : str
        Last name of the user.
    reset_password_link : AnyHttpUrl
        URL for resetting the password.
    expiration_time : int
        Expiration time for the reset password link in seconds.
    """
    to: list[str]
    subject: str
    user_first_name: str
    user_last_name: str
    reset_password_link: AnyHttpUrl
    expiration_time: int


class MqUserCreatedPayload(MqBaseSchema):
    """
    Payload for a newly created Auth user.

    `organization_guid` and `created_by_guid` are set only when a MANAGER is
    provisioned; older events without them remain valid.
    """

    id: int
    guid: UUID
    email: EmailStr
    username: str
    first_name: str | None = None
    last_name: str | None = None
    role: UserType = UserType.CUSTOMER
    organization_guid: UUID | None = None
    created_by_guid: UUID | None = None


class MqDomainEvent(MqBaseSchema):
    """
    Envelope for inter-service domain events.
    """

    event_id: UUID
    event_type: str
    occurred_at: datetime
    payload: dict[str, Any]
    retry_count: int = 0



class MqBookingEmailMessage(MqBaseSchema):
    """
    Fields shared by the booking emails sent to a booking's primary guest.

    Dates are ISO dates; `total_amount` is a decimal string with two places.
    No ID proof numbers or other guests' details are ever included.

    Attributes
    ----------
    to : list[str]
        The primary guest's email address.
    subject : str
        Subject line of the email.
    guest_first_name : str
        The primary guest's first name.
    organization_name : str
        Name of the guest house organization.
    booking_reference : str
        Booking reference such as "BK-2026-000123".
    room_number : str
        Booked room number.
    room_type_name : str
        Booked room's type.
    check_in_date, check_out_date : date
        Stay dates.
    nights : int
        Number of nights.
    guest_count : int
        Number of guests.
    total_amount : Decimal
        Price of the stay.
    currency_code : str
        ISO currency code of `total_amount`.
    """

    to: list[str]
    subject: str
    guest_first_name: str
    organization_name: str
    booking_reference: str
    room_number: str
    room_type_name: str
    check_in_date: date
    check_out_date: date
    nights: int
    guest_count: int
    total_amount: Decimal
    currency_code: str


class MqBookingConfirmedEmailMessage(MqBookingEmailMessage):
    """Booking confirmation email, sent when a booking is created."""


class MqBookingUpdatedEmailMessage(MqBookingEmailMessage):
    """
    Booking update email, sent when a booking's room or dates change.

    Attributes
    ----------
    previous_room_number : str
        Room before the change.
    previous_check_in_date, previous_check_out_date : date
        Stay dates before the change.
    """

    previous_room_number: str
    previous_check_in_date: date
    previous_check_out_date: date


class MqBookingCancelledEmailMessage(MqBookingEmailMessage):
    """
    Booking cancellation email.

    Attributes
    ----------
    cancellation_reason : str | None
        Reason given by staff, if any.
    """

    cancellation_reason: str | None
