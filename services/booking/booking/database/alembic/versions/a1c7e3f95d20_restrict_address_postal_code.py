"""change address postal code to integer

Revision ID: a1c7e3f95d20
Revises: 9d4e7f1a2b3c
Create Date: 2026-10-30 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1c7e3f95d20"
down_revision: str | Sequence[str] | None = "9d4e7f1a2b3c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Store the postal code as an integer."""
    op.alter_column(
        "addresses",
        "postal_code",
        existing_type=sa.String(length=20),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using="postal_code::integer",
    )


def downgrade() -> None:
    """Restore the postal code as a string."""
    op.alter_column(
        "addresses",
        "postal_code",
        existing_type=sa.Integer(),
        type_=sa.String(length=20),
        existing_nullable=False,
        postgresql_using="postal_code::varchar",
    )
