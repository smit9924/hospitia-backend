"""add users outbox

Revision ID: b7c4e91f2a10
Revises: ac6509a33344
Create Date: 2026-08-23 14:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'b7c4e91f2a10'
down_revision: Union[str, Sequence[str], None] = 'ac6509a33344'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users_outbox',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('guid', sa.Uuid(), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('username', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('first_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
    sa.Column('last_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
    sa.Column('is_processed', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_outbox_guid'), 'users_outbox', ['guid'], unique=False)
    op.create_index(op.f('ix_users_outbox_is_processed'), 'users_outbox', ['is_processed'], unique=False)
    op.create_index(op.f('ix_users_outbox_user_id'), 'users_outbox', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_users_outbox_user_id'), table_name='users_outbox')
    op.drop_index(op.f('ix_users_outbox_is_processed'), table_name='users_outbox')
    op.drop_index(op.f('ix_users_outbox_guid'), table_name='users_outbox')
    op.drop_table('users_outbox')
