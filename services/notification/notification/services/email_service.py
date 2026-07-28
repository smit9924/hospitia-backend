import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from notification.core.config import settings


def send_html_email(*, to: list[str], subject: str, body: str, ) -> None:
    """
    Send an HTML email using SMTP.

    Parameters
    ----------
    to : list[str]
        List of recipient email addresses.
    subject : str
        Subject line of the email.
    body : str
        HTML or plain text content of the email.

    returns
    -------
    None
        Sends the email to the specified recipients.

    reises
    ------
    smtplib.SMTPException
        If there is an error during the SMTP connection or sending process.
    """

    message = MIMEMultipart("alternative")

    message["From"] = settings.SMTP_FROM
    message["To"] = ", ".join(to)
    message["Subject"] = subject

    message.attach(MIMEText(body, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, ) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()

        smtp.login(
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
        )

        smtp.send_message(message)
