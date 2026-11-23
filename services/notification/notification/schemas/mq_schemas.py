from datetime import date
from decimal import Decimal

from pydantic import AnyHttpUrl

from notification.schemas.base_schemas import BaseSchema


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
    retry_count : int | None
        Application-level retry count injected on processing failure.
    """
    to: list[str]
    subject: str
    user_first_name: str
    user_last_name: str
    reset_password_link: AnyHttpUrl
    expiration_time: int
    retry_count: int | None = None


class MqVerifyEmailOtpMessage(MqBaseSchema):
    """
    Schema for MQ verify-email OTP messages.

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
    otp : str
        One-time password for email verification.
    expiration_time : int
        Expiration time for the OTP in minutes.
    retry_count : int | None
        Application-level retry count injected on processing failure.
    """
    to: list[str]
    subject: str
    user_first_name: str
    user_last_name: str
    otp: str
    expiration_time: int
    retry_count: int | None = None


class MqWelcomeEmailMessage(MqBaseSchema):
    """
    Schema for MQ welcome email messages with initial credentials.

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
    username : str
        Login username for the new account.
    password : str
        Initial plaintext password generated for the user.
    role : str
        Human-readable role label for the new account.
    retry_count : int | None
        Application-level retry count injected on processing failure.
    """

    to: list[str]
    subject: str
    user_first_name: str
    user_last_name: str
    username: str
    password: str
    role: str
    retry_count: int | None = None


class MqBookingEmailMessage(MqBaseSchema):
    """
    Fields shared by the booking emails sent to a booking's primary guest.

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
    retry_count : int | None
        Application-level retry count injected on processing failure.
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
    retry_count: int | None = None


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

    cancellation_reason: str | None = None
