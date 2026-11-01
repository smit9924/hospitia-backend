"""create rooms table

Revision ID: f7b9d1e3a5c6
Revises: e6a8c0d2f4b5
Create Date: 2026-11-01 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f7b9d1e3a5c6"
down_revision: str | Sequence[str] | None = "e6a8c0d2f4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the rooms table with its checks and indexes."""
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guid", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("room_type_id", sa.Integer(), nullable=False),
        sa.Column("room_number", sa.String(length=20), nullable=False),
        sa.Column("floor", sa.SmallInteger(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.CheckConstraint("floor BETWEEN -500 AND 500", name="ck_rooms_floor_range"),
        sa.CheckConstraint(
            "status IN ('available', 'under_maintenance', 'out_of_service')",
            name="ck_rooms_status",
        ),
        # PostgreSQL regex; the API validates the same rule for every database.
        sa.CheckConstraint("room_number ~ '^[A-Za-z0-9/-]{1,20}$'", name="ck_rooms_room_number_format"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["room_type_id"], ["room_types.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["usersreplica.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["usersreplica.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rooms_id"), "rooms", ["id"], unique=False)
    op.create_index(op.f("ix_rooms_guid"), "rooms", ["guid"], unique=True)
    op.create_index(op.f("ix_rooms_organization_id"), "rooms", ["organization_id"], unique=False)
    op.create_index(op.f("ix_rooms_room_type_id"), "rooms", ["room_type_id"], unique=False)
    op.create_index(op.f("ix_rooms_room_number"), "rooms", ["room_number"], unique=False)
    op.create_index(op.f("ix_rooms_is_active"), "rooms", ["is_active"], unique=False)
    op.create_index(op.f("ix_rooms_created_by"), "rooms", ["created_by"], unique=False)
    op.create_index(op.f("ix_rooms_updated_by"), "rooms", ["updated_by"], unique=False)
    # Case-insensitive room number uniqueness among an organization's active rooms.
    op.create_index(
        "uq_rooms_active_organization_room_number",
        "rooms",
        ["organization_id", sa.text("lower(room_number)")],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )


def downgrade() -> None:
    """Drop the rooms table and its indexes."""
    op.drop_index("uq_rooms_active_organization_room_number", table_name="rooms")
    op.drop_index(op.f("ix_rooms_updated_by"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_created_by"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_is_active"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_room_number"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_room_type_id"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_organization_id"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_guid"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_id"), table_name="rooms")
    op.drop_table("rooms")
