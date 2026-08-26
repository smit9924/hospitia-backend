"""add role to users_outbox

Revision ID: e1a2b3c4d5e6
Revises: b7c4e91f2a10
Create Date: 2026-08-23 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'b7c4e91f2a10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users_outbox',
        sa.Column('role', sa.Integer(), nullable=False, server_default='4'),
    )
    op.alter_column('users_outbox', 'role', server_default=None)


def downgrade() -> None:
    op.drop_column('users_outbox', 'role')
