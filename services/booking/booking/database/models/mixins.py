import uuid
from datetime import UTC, datetime

from sqlmodel import Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class GUIDMixin:
    """
    Adds a public-facing, unique GUID identifier to a model.

    `guid` should always be used for external references and API responses;
    the model's internal `id` primary key must never be exposed.
    """

    guid: uuid.UUID | None = Field(default_factory=uuid.uuid4, unique=True, nullable=False, index=True)


class AuditMixin:
    """
    Adds creation/modification audit fields to a model.

    `created_by`/`updated_by` are nullable at the database level only to
    allow system/migration-inserted rows (e.g. the default "OTHER" organization
    type) with no authenticated actor. Every API-driven create/update must
    set both explicitly at the service layer; `created_by` and `updated_by`
    are set to the same actor on creation.
    """

    created_at: datetime = Field(default_factory=_utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=_utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": _utc_now},
    )
    created_by: int | None = Field(default=None, foreign_key="usersreplica.id", nullable=True, index=True)
    updated_by: int | None = Field(default=None, foreign_key="usersreplica.id", nullable=True, index=True)


__all__ = [
    "GUIDMixin",
    "AuditMixin",
]
