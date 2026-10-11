"""add role to usersreplica

Revision ID: 7a1e2c9f4b3d
Revises: 6236ca5642cf
Create Date: 2026-09-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '7a1e2c9f4b3d'
down_revision: Union[str, Sequence[str], None] = '6236ca5642cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('usersreplica', sa.Column('role', sa.Integer(), nullable=False, server_default='4'))
    op.create_index(op.f('ix_usersreplica_role'), 'usersreplica', ['role'], unique=False)
    op.alter_column('usersreplica', 'role', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_usersreplica_role'), table_name='usersreplica')
    op.drop_column('usersreplica', 'role')
