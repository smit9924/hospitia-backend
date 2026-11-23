"""
Booking emails to the primary guest.

Messages go to the notification service through the MQ abstraction once
the booking change is committed. Emails are informative, so they are handed
to the background publisher: the request never waits for the broker, and a
failed publish is only logged (with the booking reference, never guest
data); it never fails or undoes the booking operation.
"""

from dataclasses import dataclass
from datetime import date

from booking.core.config import settings
from booking.database.models.booking import Booking
from booking.database.models.guest_detail import GuestDetail
from booking.messaging.background_publisher import get_background_publisher
from booking.schemas.mq_schemas import (
    MqBookingCancelledEmailMessage,
    MqBookingConfirmedEmailMessage,
    MqBookingEmailMessage,
    MqBookingUpdatedEmailMessage,
)


@dataclass(frozen=True)
class BookingStaySnapshot:
    """
    A booking's room and dates before an update, for the update email.

    Attributes
    ----------
    room_number : str
    check_in_date : date
    check_out_date : date
    """

    room_number: str
    check_in_date: date
    check_out_date: date

    @classmethod
    def of(cls, booking: Booking) -> "BookingStaySnapshot":
        """Capture the booking's current room and dates."""
        return cls(
            room_number=booking.room.room_number,
            check_in_date=booking.check_in_date,
            check_out_date=booking.check_out_date,
        )


def _common_fields(*, booking: Booking, primary_guest: GuestDetail, subject: str) -> dict[str, object]:
    """Build the fields every booking email shares."""
    return {
        "to": [primary_guest.email],
        "subject": subject,
        "guest_first_name": primary_guest.first_name,
        "organization_name": booking.organization.name,
        "booking_reference": booking.reference,
        "room_number": booking.room.room_number,
        "room_type_name": booking.room.room_type.name,
        "check_in_date": booking.check_in_date,
        "check_out_date": booking.check_out_date,
        "nights": booking.nights,
        "guest_count": booking.guest_count,
        "total_amount": booking.total_amount,
        "currency_code": booking.currency_unit.currency_code,
    }


def _publish(*, queue: str, message: MqBookingEmailMessage) -> None:
    """Hand a booking email to the background publisher; the request never waits for the broker."""
    get_background_publisher().submit(
        destination=queue,
        message=message,
        log_label=f"booking_reference={message.booking_reference}",
    )


def send_booking_confirmed_email(*, booking: Booking, primary_guest: GuestDetail | None) -> None:
    """Send the confirmation email when the primary guest has an email address.

    Parameters
    ----------
    booking : Booking
        The committed booking, with its organization, room, room type and
        currency loaded.
    primary_guest : GuestDetail | None
        The booking's primary guest.
    """
    if primary_guest is None or not primary_guest.email:
        return
    subject = f"Booking confirmed – {booking.reference} at {booking.organization.name}"
    message = MqBookingConfirmedEmailMessage(**_common_fields(booking=booking, primary_guest=primary_guest, subject=subject))  # type: ignore[arg-type]
    _publish(queue=settings.BOOKING_CONFIRMED_EMAIL_QUEUE, message=message)


def send_booking_updated_email(
    *,
    booking: Booking,
    primary_guest: GuestDetail | None,
    previous: BookingStaySnapshot,
) -> None:
    """Send the update email when the room or dates changed and the primary guest has an email.

    Parameters
    ----------
    booking : Booking
        The committed booking.
    primary_guest : GuestDetail | None
        The booking's primary guest.
    previous : BookingStaySnapshot
        Room and dates before the update.
    """
    if primary_guest is None or not primary_guest.email:
        return
    if previous == BookingStaySnapshot.of(booking):
        return
    message = MqBookingUpdatedEmailMessage(
        **_common_fields(booking=booking, primary_guest=primary_guest, subject=f"Booking updated – {booking.reference}"),  # type: ignore[arg-type]
        previous_room_number=previous.room_number,
        previous_check_in_date=previous.check_in_date,
        previous_check_out_date=previous.check_out_date,
    )
    _publish(queue=settings.BOOKING_UPDATED_EMAIL_QUEUE, message=message)


def send_booking_cancelled_email(*, booking: Booking, primary_guest: GuestDetail | None) -> None:
    """Send the cancellation email when the primary guest has an email address.

    Parameters
    ----------
    booking : Booking
        The committed, cancelled booking.
    primary_guest : GuestDetail | None
        The booking's primary guest.
    """
    if primary_guest is None or not primary_guest.email:
        return
    message = MqBookingCancelledEmailMessage(
        **_common_fields(booking=booking, primary_guest=primary_guest, subject=f"Booking cancelled – {booking.reference}"),  # type: ignore[arg-type]
        cancellation_reason=booking.cancellation_reason,
    )
    _publish(queue=settings.BOOKING_CANCELLED_EMAIL_QUEUE, message=message)


__all__ = [
    "BookingStaySnapshot",
    "send_booking_cancelled_email",
    "send_booking_confirmed_email",
    "send_booking_updated_email",
]
