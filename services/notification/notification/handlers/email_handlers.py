import logging
from typing import Any

from notification.schemas.mq_schemas import MqForgotPasswordMessage, MqVerifyEmailOtpMessage
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

    log.info(f"Email sent to {data.to} with subject '{data.subject}'")


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

    log.info(f"Email sent to {data.to} with subject '{data.subject}'")
