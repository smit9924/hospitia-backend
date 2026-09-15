from datetime import UTC, datetime

from sqlmodel import Field

from .base import SQLModel


class Otp(SQLModel, table=True):
    """
    Database model for one-time passwords used in email verification.

    Attributes
    ----------
    id : int | None
        Primary key identifier for the OTP record.
    user_id : int
        Foreign key reference to the associated user (`users.id`).
    otp : str
        The plaintext OTP value sent to the user.
    used : bool, default=False
        Whether the OTP has already been consumed or invalidated.
    expires_at : datetime
        UTC timestamp indicating when the OTP becomes invalid.
    created_at : datetime
        Timestamp indicating when the OTP was generated.
    """

    __tablename__ = "otp"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
    )

    otp: str = Field(
        nullable=False,
        max_length=32,
    )

    used: bool = Field(
        default=False,
        nullable=False,
    )

    expires_at: datetime = Field(
        nullable=False,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )


__all__ = [
    "Otp",
]
