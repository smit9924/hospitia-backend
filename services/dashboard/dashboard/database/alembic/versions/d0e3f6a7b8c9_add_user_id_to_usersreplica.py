"""add user_id to usersreplica

Revision ID: d0e3f6a7b8c9
Revises: a5f02c467b7d
Create Date: 2026-08-16 13:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd0e3f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'a5f02c467b7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usersreplica', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_index(op.f('ix_usersreplica_user_id'), 'usersreplica', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_usersreplica_user_id'), table_name='usersreplica')
    op.drop_column('usersreplica', 'user_id')
