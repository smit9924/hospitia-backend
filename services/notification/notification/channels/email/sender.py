import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from notification.core.config import settings


def send_email(
    *,
    to: list[str],
    subject: str,
    html: str,
) -> None:
    """
    Send an HTML email via SMTP.

    Parameters
    ----------
    to : list[str]
        Recipient email addresses.
    subject : str
        Email subject line.
    html : str
        Rendered HTML body content.
    """
    msg = MIMEMultipart("alternative")
    msg["From"] = settings.smtp_from
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject

    msg.attach(MIMEText(html, "html"))

    server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
    if settings.smtp_use_tls:
        server.starttls()

    server.login(settings.smtp_username, settings.smtp_password)
    server.send_message(msg)
    server.quit()
