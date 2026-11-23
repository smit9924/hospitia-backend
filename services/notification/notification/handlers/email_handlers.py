import logging
from datetime import date
from typing import Any

from notification.schemas.mq_schemas import (
    MqBookingCancelledEmailMessage,
    MqBookingConfirmedEmailMessage,
    MqBookingEmailMessage,
    MqBookingUpdatedEmailMessage,
    MqForgotPasswordMessage,
    MqVerifyEmailOtpMessage,
    MqWelcomeEmailMessage,
)
from notification.services.email_service import send_html_email
from notification.services.template_service import render_template

log = logging.getLogger(__name__)


def forgot_password_email_handler(event: dict[str, Any]) -> None:
    """
    Handle the forgot password email event.

    Parameters
    ----------
    event : dict[str, Any]
        The event data containing the email details and user information.

    returns
    -------
    None
    """
    log.info("Started")
    data = MqForgotPasswordMessage(**event)

    html = render_template(
        "forgot_password_email.html",
        data.model_dump(),
    )

    send_html_email(
        to=data.to,
        subject=data.subject,
        body=html,
    )

    log.info(
        "Forgot password email sent recipient_count=%d subject=%s",
        len(data.to),
        data.subject,
    )


def verify_email_otp_email_handler(event: dict[str, Any]) -> None:
    """
    Handle the verify-email OTP email event.

    Parameters
    ----------
    event : dict[str, Any]
        The event data containing the email details and OTP information.

    returns
    -------
    None
    """
    log.info("Started")
    data = MqVerifyEmailOtpMessage(**event)

    html = render_template(
        "verify_email_otp_email.html",
        data.model_dump(),
    )

    send_html_email(
        to=data.to,
        subject=data.subject,
        body=html,
    )

    log.info(
        "Verify email OTP email sent recipient_count=%d subject=%s",
        len(data.to),
        data.subject,
    )


def welcome_email_handler(event: dict[str, Any]) -> None:
    """
    Handle the welcome email event for newly created users.

    Parameters
    ----------
    event : dict[str, Any]
        The event data containing credentials and user information.

    returns
    -------
    None
    """
    log.info("Started")
    data = MqWelcomeEmailMessage(**event)

    html = render_template(
        "welcome_email.html",
        data.model_dump(),
    )

    send_html_email(
        to=data.to,
        subject=data.subject,
        body=html,
    )

    log.info(
        "Welcome email sent recipient_count=%d subject=%s",
        len(data.to),
        data.subject,
    )


def _format_date(value: date) -> str:
    """Format a stay date for emails, e.g. "12 Dec 2026"."""
    return f"{value.day} {value:%b %Y}"


def _booking_template_data(data: MqBookingEmailMessage) -> dict[str, Any]:
    """Return the message fields plus the formatted labels the booking templates show."""
    return {
        **data.model_dump(),
        "check_in_label": _format_date(data.check_in_date),
        "check_out_label": _format_date(data.check_out_date),
        "total_label": f"{data.currency_code} {data.total_amount:,.2f}",
    }


def _send_booking_email(*, template_name: str, data: MqBookingEmailMessage, extra: dict[str, Any] | None = None) -> None:
    """Render a booking template and send it to the primary guest."""
    html = render_template(template_name, {**_booking_template_data(data), **(extra or {})})
    send_html_email(to=data.to, subject=data.subject, body=html)
    log.info(
        "Booking email sent template_name=%s booking_reference=%s",
        template_name,
        data.booking_reference,
    )


def booking_confirmed_email_handler(event: dict[str, Any]) -> None:
    """
    Handle the booking confirmed event: email the stay details to the primary guest.

    Parameters
    ----------
    event : dict[str, Any]
        The event data matching `MqBookingConfirmedEmailMessage`.

    returns
    -------
    None
    """
    log.info("Started")
    _send_booking_email(
        template_name="booking_confirmed_email.html",
        data=MqBookingConfirmedEmailMessage(**event),
    )


def booking_updated_email_handler(event: dict[str, Any]) -> None:
    """
    Handle the booking updated event: email the new and previous stay to the primary guest.

    Parameters
    ----------
    event : dict[str, Any]
        The event data matching `MqBookingUpdatedEmailMessage`.

    returns
    -------
    None
    """
    log.info("Started")
    data = MqBookingUpdatedEmailMessage(**event)
    _send_booking_email(
        template_name="booking_updated_email.html",
        data=data,
        extra={
            "previous_check_in_label": _format_date(data.previous_check_in_date),
            "previous_check_out_label": _format_date(data.previous_check_out_date),
        },
    )


def booking_cancelled_email_handler(event: dict[str, Any]) -> None:
    """
    Handle the booking cancelled event: email the cancelled stay (and reason) to the primary guest.

    Parameters
    ----------
    event : dict[str, Any]
        The event data matching `MqBookingCancelledEmailMessage`.

    returns
    -------
    None
    """
    log.info("Started")
    _send_booking_email(
        template_name="booking_cancelled_email.html",
        data=MqBookingCancelledEmailMessage(**event),
    )
