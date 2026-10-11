"""create addresses table

Revision ID: 9c3f7d21a8e4
Revises: 7a1e2c9f4b3d
Create Date: 2026-09-19 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '9c3f7d21a8e4'
down_revision: Union[str, Sequence[str], None] = '7a1e2c9f4b3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'addresses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guid', sa.Uuid(), nullable=False),
        sa.Column('address_line_1', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('address_line_2', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('landmark', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('city', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('state', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('country', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('postal_code', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['usersreplica.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['usersreplica.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_addresses_id'), 'addresses', ['id'], unique=False)
    op.create_index(op.f('ix_addresses_guid'), 'addresses', ['guid'], unique=True)
    op.create_index(op.f('ix_addresses_city'), 'addresses', ['city'], unique=False)
    op.create_index(op.f('ix_addresses_state'), 'addresses', ['state'], unique=False)
    op.create_index(op.f('ix_addresses_country'), 'addresses', ['country'], unique=False)
    op.create_index(op.f('ix_addresses_created_by'), 'addresses', ['created_by'], unique=False)
    op.create_index(op.f('ix_addresses_updated_by'), 'addresses', ['updated_by'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_addresses_updated_by'), table_name='addresses')
    op.drop_index(op.f('ix_addresses_created_by'), table_name='addresses')
    op.drop_index(op.f('ix_addresses_country'), table_name='addresses')
    op.drop_index(op.f('ix_addresses_state'), table_name='addresses')
    op.drop_index(op.f('ix_addresses_city'), table_name='addresses')
    op.drop_index(op.f('ix_addresses_guid'), table_name='addresses')
    op.drop_index(op.f('ix_addresses_id'), table_name='addresses')
    op.drop_table('addresses')
