import logging

from notification.channels.email.sender import send_email
from notification.channels.email.template import render_template
from notification.schemas.email import EmailPayload
from notification.schemas.event import NotificationEvent

log = logging.getLogger(__name__)


def handle(event: NotificationEvent) -> None:
    """
    Process an email notification event.

    Workflow
    --------
    - Validate incoming payload using EmailPayload schema.
    - Render HTML content from the configured template.
    - Send email via SMTP sender.

    Parameters
    ----------
    payload : dict[str, object]
        Raw event payload received from the notification consumer.

    Raises
    ------
    ValidationError
        If payload structure does not match EmailPayload schema.
    """
    email = EmailPayload(**event.payload)

    html = render_template(
        email.template,
        email.data,
    )

    send_email(
        to=email.to,
        subject=email.subject,
        html=html,
    )

    log.info(f"Email sent to {email.to} with subject '{email.subject}'")
