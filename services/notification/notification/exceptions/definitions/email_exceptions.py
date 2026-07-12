from notification.exceptions.definitions.base import BaseException


class SmtpAuthenticationError(BaseException):
    """
    Raised when SMTP login fails due to invalid credentials.
    """

    def __init__(self, message: str = "Invalid SMTP credentials.") -> None:
        super().__init__(message)


class SmtpConnectionError(BaseException):
    """
    Raised when the SMTP server is unreachable or the connection
    is refused.
    """

    def __init__(self, message: str = "Unable to connect to SMTP server.") -> None:
        super().__init__(message)


class SmtpTransmissionError(BaseException):
    """
    Raised when the email is partially accepted or the DATA command
    fails mid-transmission. Treated as transient.
    """

    def __init__(self, message: str = "Failed to transmit email via SMTP.") -> None:
        super().__init__(message)
