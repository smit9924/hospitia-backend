import uuid

from pydantic import EmailStr
from sqlmodel import Boolean, Field

from .base import SQLModel


class UsersOutbox(SQLModel, table=True):
    """
    Database model for the user-created transactional outbox.

    Stores a snapshot of user details that must be published after the
    user row is committed. Broker topology is not stored here; the outbox
    worker already knows how to publish the event.

    Attributes
    ----------
    id : int | None
        Primary key identifier for the outbox record.
    user_id : int
        Auth service primary key of the created user.
    guid : uuid.UUID
        Public user identifier used in JWTs and APIs.
    email : EmailStr
        Unique email address of the created user.
    username : str
        Unique username of the created user.
    first_name : str | None, optional
        User's first name.
    last_name : str | None, optional
        User's last name.
    is_processed : bool, default=False
        Whether the outbox worker has successfully published this row.
    """

    __tablename__ = "users_outbox"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(nullable=False, index=True)

    guid: uuid.UUID = Field(nullable=False, index=True)

    email: EmailStr = Field(max_length=255, nullable=False)

    username: str = Field(max_length=255, nullable=False)

    first_name: str | None = Field(default=None, max_length=255)

    last_name: str | None = Field(default=None, max_length=255)

    is_processed: bool = Field(
        default=False,
        nullable=False,
        sa_type=Boolean,
        index=True,
    )


__all__ = [
    "UsersOutbox",
]
