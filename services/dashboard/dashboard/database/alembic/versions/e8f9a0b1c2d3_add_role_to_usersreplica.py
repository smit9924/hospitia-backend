"""add role to usersreplica

Revision ID: e8f9a0b1c2d3
Revises: d0e3f6a7b8c9
Create Date: 2026-08-23 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e8f9a0b1c2d3'
down_revision: Union[str, Sequence[str], None] = 'd0e3f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'usersreplica',
        sa.Column('role', sa.Integer(), nullable=False, server_default='4'),
    )
    op.create_index(op.f('ix_usersreplica_role'), 'usersreplica', ['role'], unique=False)
    op.alter_column('usersreplica', 'role', server_default=None)


def downgrade() -> None:
    op.drop_index(op.f('ix_usersreplica_role'), table_name='usersreplica')
    op.drop_column('usersreplica', 'role')
