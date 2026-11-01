"""create room amenities table

Revision ID: d5f7b9c1e3a4
Revises: c4e6a8b0d2f3
Create Date: 2026-10-31 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d5f7b9c1e3a4"
down_revision: str | Sequence[str] | None = "c4e6a8b0d2f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the room amenities table (default and organization-specific amenities)."""
    op.create_table(
        "room_amenities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guid", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["usersreplica.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["usersreplica.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_room_amenities_id"), "room_amenities", ["id"], unique=False)
    op.create_index(op.f("ix_room_amenities_guid"), "room_amenities", ["guid"], unique=True)
    op.create_index(op.f("ix_room_amenities_name"), "room_amenities", ["name"], unique=False)
    op.create_index(op.f("ix_room_amenities_organization_id"), "room_amenities", ["organization_id"], unique=False)
    op.create_index(op.f("ix_room_amenities_is_active"), "room_amenities", ["is_active"], unique=False)
    op.create_index(op.f("ix_room_amenities_created_by"), "room_amenities", ["created_by"], unique=False)
    op.create_index(op.f("ix_room_amenities_updated_by"), "room_amenities", ["updated_by"], unique=False)
    # Case-insensitive name uniqueness among active rows: once across the
    # defaults, and once per organization across its custom amenities.
    op.create_index(
        "uq_room_amenities_active_default_name",
        "room_amenities",
        [sa.text("lower(name)")],
        unique=True,
        postgresql_where=sa.text("is_active AND organization_id IS NULL"),
    )
    op.create_index(
        "uq_room_amenities_active_custom_name",
        "room_amenities",
        ["organization_id", sa.text("lower(name)")],
        unique=True,
        postgresql_where=sa.text("is_active AND organization_id IS NOT NULL"),
    )


def downgrade() -> None:
    """Drop the room amenities table."""
    op.drop_index("uq_room_amenities_active_custom_name", table_name="room_amenities")
    op.drop_index("uq_room_amenities_active_default_name", table_name="room_amenities")
    op.drop_index(op.f("ix_room_amenities_updated_by"), table_name="room_amenities")
    op.drop_index(op.f("ix_room_amenities_created_by"), table_name="room_amenities")
    op.drop_index(op.f("ix_room_amenities_is_active"), table_name="room_amenities")
    op.drop_index(op.f("ix_room_amenities_organization_id"), table_name="room_amenities")
    op.drop_index(op.f("ix_room_amenities_name"), table_name="room_amenities")
    op.drop_index(op.f("ix_room_amenities_guid"), table_name="room_amenities")
    op.drop_index(op.f("ix_room_amenities_id"), table_name="room_amenities")
    op.drop_table("room_amenities")
