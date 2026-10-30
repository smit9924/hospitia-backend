"""add organization_guid and created_by_guid to users_outbox

Revision ID: a9d3e5f7b1c2
Revises: f2b3c4d5e6f7
Create Date: 2026-10-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a9d3e5f7b1c2'
down_revision: Union[str, Sequence[str], None] = 'f2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users_outbox',
        sa.Column('organization_guid', sa.Uuid(), nullable=True),
    )
    op.add_column(
        'users_outbox',
        sa.Column('created_by_guid', sa.Uuid(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('users_outbox', 'created_by_guid')
    op.drop_column('users_outbox', 'organization_guid')
