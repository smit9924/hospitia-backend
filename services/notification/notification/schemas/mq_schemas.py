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
