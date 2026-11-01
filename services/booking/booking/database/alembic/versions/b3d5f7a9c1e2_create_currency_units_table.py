"""create currency units table

Revision ID: b3d5f7a9c1e2
Revises: a1c7e3f95d20
Create Date: 2026-10-31 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b3d5f7a9c1e2"
down_revision: str | Sequence[str] | None = "a1c7e3f95d20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the ISO 4217 currency units table."""
    op.create_table(
        "currency_units",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guid", sa.Uuid(), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("numeric_code", sa.String(length=3), nullable=False),
        sa.Column("currency_name", sa.String(length=100), nullable=False),
        sa.Column("minor_unit", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["usersreplica.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["usersreplica.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_currency_units_id"), "currency_units", ["id"], unique=False)
    op.create_index(op.f("ix_currency_units_guid"), "currency_units", ["guid"], unique=True)
    op.create_index(op.f("ix_currency_units_currency_code"), "currency_units", ["currency_code"], unique=False)
    op.create_index(op.f("ix_currency_units_currency_name"), "currency_units", ["currency_name"], unique=False)
    op.create_index(op.f("ix_currency_units_is_active"), "currency_units", ["is_active"], unique=False)
    op.create_index(op.f("ix_currency_units_created_by"), "currency_units", ["created_by"], unique=False)
    op.create_index(op.f("ix_currency_units_updated_by"), "currency_units", ["updated_by"], unique=False)
    # Codes are unique among active rows only, so a deleted currency can be re-added.
    op.create_index(
        "uq_currency_units_active_currency_code",
        "currency_units",
        ["currency_code"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )
    op.create_index(
        "uq_currency_units_active_numeric_code",
        "currency_units",
        ["numeric_code"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )


def downgrade() -> None:
    """Drop the currency units table."""
    op.drop_index("uq_currency_units_active_numeric_code", table_name="currency_units")
    op.drop_index("uq_currency_units_active_currency_code", table_name="currency_units")
    op.drop_index(op.f("ix_currency_units_updated_by"), table_name="currency_units")
    op.drop_index(op.f("ix_currency_units_created_by"), table_name="currency_units")
    op.drop_index(op.f("ix_currency_units_is_active"), table_name="currency_units")
    op.drop_index(op.f("ix_currency_units_currency_name"), table_name="currency_units")
    op.drop_index(op.f("ix_currency_units_currency_code"), table_name="currency_units")
    op.drop_index(op.f("ix_currency_units_guid"), table_name="currency_units")
    op.drop_index(op.f("ix_currency_units_id"), table_name="currency_units")
    op.drop_table("currency_units")
