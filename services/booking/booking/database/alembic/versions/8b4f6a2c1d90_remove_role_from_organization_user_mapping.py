"""remove role from organization user mapping

Revision ID: 8b4f6a2c1d90
Revises: 6d9e1a4f7b32
Create Date: 2026-10-06 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8b4f6a2c1d90"
down_revision: str | Sequence[str] | None = "6d9e1a4f7b32"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove the role duplicated from usersreplica."""
    op.drop_constraint(
        "uq_org_user_mapping_org_user_role",
        "organization_user_mapping",
        type_="unique",
    )
    op.drop_index("ix_organization_user_mapping_role", table_name="organization_user_mapping")
    op.drop_column("organization_user_mapping", "role")
    op.create_unique_constraint(
        "uq_org_user_mapping_org_user",
        "organization_user_mapping",
        ["organization_id", "user_id"],
    )


def downgrade() -> None:
    """Restore role from usersreplica before reinstating the old constraint."""
    op.drop_constraint("uq_org_user_mapping_org_user", "organization_user_mapping", type_="unique")
    op.add_column("organization_user_mapping", sa.Column("role", sa.Integer(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE organization_user_mapping AS mapping
            SET role = users.role
            FROM usersreplica AS users
            WHERE users.id = mapping.user_id
            """
        )
    )
    op.alter_column("organization_user_mapping", "role", nullable=False)
    op.create_index("ix_organization_user_mapping_role", "organization_user_mapping", ["role"], unique=False)
    op.create_unique_constraint(
        "uq_org_user_mapping_org_user_role",
        "organization_user_mapping",
        ["organization_id", "user_id", "role"],
    )
