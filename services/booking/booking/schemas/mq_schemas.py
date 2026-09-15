from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import AnyHttpUrl, EmailStr

from booking.schemas.base_schemas import BaseSchema


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
    """

    id: int
    guid: UUID
    email: EmailStr
    username: str
    first_name: str | None = None
    last_name: str | None = None


class MqDomainEvent(MqBaseSchema):
    """
    Envelope for inter-service domain events.
    """

    event_id: UUID
    event_type: str
    occurred_at: datetime
    payload: dict[str, Any]
    retry_count: int = 0

