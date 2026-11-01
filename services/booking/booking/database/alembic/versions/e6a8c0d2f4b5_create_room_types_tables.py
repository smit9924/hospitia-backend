"""create room types and room type amenity mappings tables

Revision ID: e6a8c0d2f4b5
Revises: d5f7b9c1e3a4
Create Date: 2026-10-31 14:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e6a8c0d2f4b5"
down_revision: str | Sequence[str] | None = "d5f7b9c1e3a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the room types table and its amenity mapping table."""
    op.create_table(
        "room_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guid", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("cost_per_night", sa.Numeric(precision=11, scale=2), nullable=False),
        sa.Column("currency_unit_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.CheckConstraint("capacity BETWEEN 1 AND 1000", name="ck_room_types_capacity_range"),
        sa.CheckConstraint(
            "cost_per_night >= 0 AND cost_per_night <= 999999999.99",
            name="ck_room_types_cost_per_night_range",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["currency_unit_id"], ["currency_units.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["usersreplica.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["usersreplica.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_room_types_id"), "room_types", ["id"], unique=False)
    op.create_index(op.f("ix_room_types_guid"), "room_types", ["guid"], unique=True)
    op.create_index(op.f("ix_room_types_organization_id"), "room_types", ["organization_id"], unique=False)
    op.create_index(op.f("ix_room_types_name"), "room_types", ["name"], unique=False)
    op.create_index(op.f("ix_room_types_currency_unit_id"), "room_types", ["currency_unit_id"], unique=False)
    op.create_index(op.f("ix_room_types_is_active"), "room_types", ["is_active"], unique=False)
    op.create_index(op.f("ix_room_types_created_by"), "room_types", ["created_by"], unique=False)
    op.create_index(op.f("ix_room_types_updated_by"), "room_types", ["updated_by"], unique=False)
    # Case-insensitive name uniqueness among an organization's active room types.
    op.create_index(
        "uq_room_types_active_organization_name",
        "room_types",
        ["organization_id", sa.text("lower(name)")],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )

    op.create_table(
        "room_type_amenity_mappings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_type_id", sa.Integer(), nullable=False),
        sa.Column("room_amenity_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["room_type_id"], ["room_types.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["room_amenity_id"], ["room_amenities.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["usersreplica.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["usersreplica.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_type_id", "room_amenity_id", name="uq_room_type_amenity_mappings_room_type_amenity"),
    )
    op.create_index(op.f("ix_room_type_amenity_mappings_id"), "room_type_amenity_mappings", ["id"], unique=False)
    op.create_index(
        op.f("ix_room_type_amenity_mappings_room_type_id"), "room_type_amenity_mappings", ["room_type_id"], unique=False
    )
    op.create_index(
        op.f("ix_room_type_amenity_mappings_room_amenity_id"),
        "room_type_amenity_mappings",
        ["room_amenity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_room_type_amenity_mappings_created_by"), "room_type_amenity_mappings", ["created_by"], unique=False
    )
    op.create_index(
        op.f("ix_room_type_amenity_mappings_updated_by"), "room_type_amenity_mappings", ["updated_by"], unique=False
    )


def downgrade() -> None:
    """Drop the room type amenity mappings and room types tables."""
    op.drop_index(op.f("ix_room_type_amenity_mappings_updated_by"), table_name="room_type_amenity_mappings")
    op.drop_index(op.f("ix_room_type_amenity_mappings_created_by"), table_name="room_type_amenity_mappings")
    op.drop_index(op.f("ix_room_type_amenity_mappings_room_amenity_id"), table_name="room_type_amenity_mappings")
    op.drop_index(op.f("ix_room_type_amenity_mappings_room_type_id"), table_name="room_type_amenity_mappings")
    op.drop_index(op.f("ix_room_type_amenity_mappings_id"), table_name="room_type_amenity_mappings")
    op.drop_table("room_type_amenity_mappings")

    op.drop_index("uq_room_types_active_organization_name", table_name="room_types")
    op.drop_index(op.f("ix_room_types_updated_by"), table_name="room_types")
    op.drop_index(op.f("ix_room_types_created_by"), table_name="room_types")
    op.drop_index(op.f("ix_room_types_is_active"), table_name="room_types")
    op.drop_index(op.f("ix_room_types_currency_unit_id"), table_name="room_types")
    op.drop_index(op.f("ix_room_types_name"), table_name="room_types")
    op.drop_index(op.f("ix_room_types_organization_id"), table_name="room_types")
    op.drop_index(op.f("ix_room_types_guid"), table_name="room_types")
    op.drop_index(op.f("ix_room_types_id"), table_name="room_types")
    op.drop_table("room_types")
