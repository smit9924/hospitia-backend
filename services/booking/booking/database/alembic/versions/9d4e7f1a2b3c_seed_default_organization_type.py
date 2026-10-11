"""seed the default organization type

Revision ID: 9d4e7f1a2b3c
Revises: 8b4f6a2c1d90
Create Date: 2026-10-11 10:00:00.000000

"""
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision: str = "9d4e7f1a2b3c"
down_revision: str | Sequence[str] | None = "8b4f6a2c1d90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_ORGANIZATION_TYPE_NAME = "OTHER"
DEFAULT_ORGANIZATION_TYPE_GUID = UUID("00000000-0000-0000-0000-000000000001")


def upgrade() -> None:
    """Insert the default organization type when it does not exist."""
    organization_types = sa.table(
        "organization_types",
        sa.column("guid", sa.Uuid()),
        sa.column("name", sa.String(length=100)),
        sa.column("description", sa.String(length=500)),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
        sa.column("created_by", sa.Integer()),
        sa.column("updated_by", sa.Integer()),
    )
    bind = op.get_bind()
    existing = bind.execute(
        sa.select(organization_types.c.guid).where(
            organization_types.c.name == DEFAULT_ORGANIZATION_TYPE_NAME
        )
    ).scalar_one_or_none()
    if existing is not None:
        return

    now = datetime.now(UTC)
    op.bulk_insert(
        organization_types,
        [
            {
                "guid": DEFAULT_ORGANIZATION_TYPE_GUID,
                "name": DEFAULT_ORGANIZATION_TYPE_NAME,
                "description": "Default organization type.",
                "created_at": now,
                "updated_at": now,
                "created_by": None,
                "updated_by": None,
            }
        ],
    )


def downgrade() -> None:
    """Remove the default organization type inserted by this migration."""
    organization_types = sa.table(
        "organization_types",
        sa.column("guid", sa.Uuid()),
    )
    op.execute(
        organization_types.delete().where(
            organization_types.c.guid == DEFAULT_ORGANIZATION_TYPE_GUID
        )
    )
