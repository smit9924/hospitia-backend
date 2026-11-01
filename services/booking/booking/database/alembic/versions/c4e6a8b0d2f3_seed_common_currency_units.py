"""seed the most used currency units

Revision ID: c4e6a8b0d2f3
Revises: b3d5f7a9c1e2
Create Date: 2026-10-31 10:05:00.000000

Values come from ISO 4217 List One, kept for reference at
`booking/database/reference_data/iso_4217_currency_codes_list_one_by_www.six-group.com.xls`.

The selection is the ten most traded currencies of the BIS Triennial
Central Bank Survey 2025 (FX turnover), with INR (the application's default
currency) replacing SGD, the tenth. Admins add any other currency from the
application.
"""
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision: str = "c4e6a8b0d2f3"
down_revision: str | Sequence[str] | None = "b3d5f7a9c1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (guid, currency_code, numeric_code, currency_name, minor_unit).
# Fixed GUIDs keep the seeded rows identifiable across environments.
SEEDED_CURRENCY_UNITS: list[tuple[UUID, str, str, str, int]] = [
    (UUID("00000000-0000-0000-0001-000000000001"), "USD", "840", "US Dollar", 2),
    (UUID("00000000-0000-0000-0001-000000000002"), "EUR", "978", "Euro", 2),
    (UUID("00000000-0000-0000-0001-000000000003"), "JPY", "392", "Yen", 0),
    (UUID("00000000-0000-0000-0001-000000000004"), "GBP", "826", "Pound Sterling", 2),
    (UUID("00000000-0000-0000-0001-000000000005"), "CNY", "156", "Yuan Renminbi", 2),
    (UUID("00000000-0000-0000-0001-000000000006"), "CHF", "756", "Swiss Franc", 2),
    (UUID("00000000-0000-0000-0001-000000000007"), "AUD", "036", "Australian Dollar", 2),
    (UUID("00000000-0000-0000-0001-000000000008"), "CAD", "124", "Canadian Dollar", 2),
    (UUID("00000000-0000-0000-0001-000000000009"), "HKD", "344", "Hong Kong Dollar", 2),
    (UUID("00000000-0000-0000-0001-000000000010"), "INR", "356", "Indian Rupee", 2),
]

currency_units_table = sa.table(
    "currency_units",
    sa.column("guid", sa.Uuid()),
    sa.column("currency_code", sa.String(length=3)),
    sa.column("numeric_code", sa.String(length=3)),
    sa.column("currency_name", sa.String(length=100)),
    sa.column("minor_unit", sa.Integer()),
    sa.column("is_active", sa.Boolean()),
    sa.column("created_at", sa.DateTime()),
    sa.column("updated_at", sa.DateTime()),
    sa.column("created_by", sa.Integer()),
    sa.column("updated_by", sa.Integer()),
)


def upgrade() -> None:
    """Insert the seeded currency units whose code is not already active."""
    bind = op.get_bind()
    already_active_codes = set(
        bind.execute(
            sa.select(currency_units_table.c.currency_code).where(currency_units_table.c.is_active)
        ).scalars()
    )

    now = datetime.now(UTC)
    rows_to_insert = [
        {
            "guid": guid,
            "currency_code": currency_code,
            "numeric_code": numeric_code,
            "currency_name": currency_name,
            "minor_unit": minor_unit,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            # System-inserted rows have no authenticated actor.
            "created_by": None,
            "updated_by": None,
        }
        for guid, currency_code, numeric_code, currency_name, minor_unit in SEEDED_CURRENCY_UNITS
        if currency_code not in already_active_codes
    ]
    if rows_to_insert:
        op.bulk_insert(currency_units_table, rows_to_insert)


def downgrade() -> None:
    """Remove the currency units inserted by this migration."""
    seeded_guids = [guid for guid, *_ in SEEDED_CURRENCY_UNITS]
    op.execute(currency_units_table.delete().where(currency_units_table.c.guid.in_(seeded_guids)))
