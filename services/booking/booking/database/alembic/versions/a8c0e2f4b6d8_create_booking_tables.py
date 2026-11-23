"""create bookings, guest details and booking guest mappings tables

Revision ID: a8c0e2f4b6d8
Revises: f7b9d1e3a5c6
Create Date: 2026-11-23 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a8c0e2f4b6d8"
down_revision: str | Sequence[str] | None = "f7b9d1e3a5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Numbers the "BK-<year>-<number>" booking references.
BOOKING_REFERENCE_SEQUENCE = "booking_reference_seq"


def _audit_columns() -> list[sa.Column]:
    """Return the `AuditMixin` columns shared by the three tables."""
    return [
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
    ]


def _create_common_indexes(table: str) -> None:
    """Create the id, guid and audit indexes every table has."""
    op.create_index(op.f(f"ix_{table}_id"), table, ["id"], unique=False)
    op.create_index(op.f(f"ix_{table}_guid"), table, ["guid"], unique=True)
    op.create_index(op.f(f"ix_{table}_created_by"), table, ["created_by"], unique=False)
    op.create_index(op.f(f"ix_{table}_updated_by"), table, ["updated_by"], unique=False)


def _drop_common_indexes(table: str) -> None:
    """Drop the indexes created by `_create_common_indexes`."""
    op.drop_index(op.f(f"ix_{table}_updated_by"), table_name=table)
    op.drop_index(op.f(f"ix_{table}_created_by"), table_name=table)
    op.drop_index(op.f(f"ix_{table}_guid"), table_name=table)
    op.drop_index(op.f(f"ix_{table}_id"), table_name=table)


def upgrade() -> None:
    """Create the booking tables, their checks and indexes, and the reference sequence."""
    op.execute(sa.schema.CreateSequence(sa.Sequence(BOOKING_REFERENCE_SEQUENCE)))

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guid", sa.Uuid(), nullable=False),
        sa.Column("reference", sa.String(length=20), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("booked_by", sa.Integer(), nullable=False),
        sa.Column("booked_by_role", sa.Integer(), nullable=False),
        sa.Column("check_in_date", sa.Date(), nullable=False),
        sa.Column("check_out_date", sa.Date(), nullable=False),
        sa.Column("nights", sa.SmallInteger(), nullable=False),
        sa.Column("guest_count", sa.SmallInteger(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("cost_per_night", sa.Numeric(precision=11, scale=2), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=13, scale=2), nullable=False),
        sa.Column("currency_unit_id", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.Column("checked_in_at", sa.DateTime(), nullable=True),
        sa.Column("checked_in_by", sa.Integer(), nullable=True),
        sa.Column("checked_out_at", sa.DateTime(), nullable=True),
        sa.Column("checked_out_by", sa.Integer(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_by", sa.Integer(), nullable=True),
        sa.Column("cancellation_reason", sa.String(length=500), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint("check_out_date > check_in_date", name="ck_bookings_dates_order"),
        sa.CheckConstraint("nights BETWEEN 1 AND 90", name="ck_bookings_nights_range"),
        sa.CheckConstraint("guest_count >= 1", name="ck_bookings_guest_count_positive"),
        sa.CheckConstraint(
            "status IN ('confirmed', 'checked_in', 'checked_out', 'cancelled')",
            name="ck_bookings_status",
        ),
        sa.CheckConstraint("cost_per_night >= 0", name="ck_bookings_cost_per_night_positive"),
        sa.CheckConstraint("total_amount >= 0", name="ck_bookings_total_amount_positive"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["booked_by"], ["usersreplica.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["currency_unit_id"], ["currency_units.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["checked_in_by"], ["usersreplica.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["checked_out_by"], ["usersreplica.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cancelled_by"], ["usersreplica.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["usersreplica.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["usersreplica.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("bookings")
    op.create_index(op.f("ix_bookings_reference"), "bookings", ["reference"], unique=True)
    op.create_index(op.f("ix_bookings_organization_id"), "bookings", ["organization_id"], unique=False)
    op.create_index(op.f("ix_bookings_room_id"), "bookings", ["room_id"], unique=False)
    op.create_index(op.f("ix_bookings_booked_by"), "bookings", ["booked_by"], unique=False)
    op.create_index(op.f("ix_bookings_check_in_date"), "bookings", ["check_in_date"], unique=False)
    op.create_index(op.f("ix_bookings_currency_unit_id"), "bookings", ["currency_unit_id"], unique=False)
    # Listing filters by organization and status; availability looks up a room's stays.
    op.create_index("ix_bookings_organization_status", "bookings", ["organization_id", "status"], unique=False)
    op.create_index(
        "ix_bookings_room_stay", "bookings", ["room_id", "check_in_date", "check_out_date"], unique=False
    )

    op.create_table(
        "guest_details",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guid", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("id_proof_type", sa.String(length=30), nullable=True),
        sa.Column("id_proof_number", sa.String(length=50), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("nationality", sa.String(length=100), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "gender IN ('male', 'female', 'other', 'prefer_not_to_say')",
            name="ck_guest_details_gender",
        ),
        sa.CheckConstraint(
            "id_proof_type IS NULL OR id_proof_type IN "
            "('aadhaar', 'passport', 'driving_licence', 'voter_id', 'other')",
            name="ck_guest_details_id_proof_type",
        ),
        sa.CheckConstraint(
            "(id_proof_type IS NULL) = (id_proof_number IS NULL)",
            name="ck_guest_details_id_proof_pair",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["usersreplica.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["usersreplica.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("guest_details")
    op.create_index(op.f("ix_guest_details_organization_id"), "guest_details", ["organization_id"], unique=False)

    op.create_table(
        "booking_guest_mappings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guid", sa.Uuid(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("guest_id", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["guest_id"], ["guest_details.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["usersreplica.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["usersreplica.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_id", "position", name="uq_booking_guest_mappings_booking_position"),
    )
    _create_common_indexes("booking_guest_mappings")
    op.create_index(op.f("ix_booking_guest_mappings_booking_id"), "booking_guest_mappings", ["booking_id"], unique=False)
    op.create_index(op.f("ix_booking_guest_mappings_guest_id"), "booking_guest_mappings", ["guest_id"], unique=True)
    # One primary guest per booking.
    op.create_index(
        "uq_booking_guest_mappings_one_primary",
        "booking_guest_mappings",
        ["booking_id"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
    )


def downgrade() -> None:
    """Drop the booking tables, their indexes and the reference sequence."""
    op.drop_index("uq_booking_guest_mappings_one_primary", table_name="booking_guest_mappings")
    op.drop_index(op.f("ix_booking_guest_mappings_guest_id"), table_name="booking_guest_mappings")
    op.drop_index(op.f("ix_booking_guest_mappings_booking_id"), table_name="booking_guest_mappings")
    _drop_common_indexes("booking_guest_mappings")
    op.drop_table("booking_guest_mappings")

    op.drop_index(op.f("ix_guest_details_organization_id"), table_name="guest_details")
    _drop_common_indexes("guest_details")
    op.drop_table("guest_details")

    op.drop_index("ix_bookings_room_stay", table_name="bookings")
    op.drop_index("ix_bookings_organization_status", table_name="bookings")
    op.drop_index(op.f("ix_bookings_currency_unit_id"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_check_in_date"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_booked_by"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_room_id"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_organization_id"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_reference"), table_name="bookings")
    _drop_common_indexes("bookings")
    op.drop_table("bookings")

    op.execute(sa.schema.DropSequence(sa.Sequence(BOOKING_REFERENCE_SEQUENCE)))
