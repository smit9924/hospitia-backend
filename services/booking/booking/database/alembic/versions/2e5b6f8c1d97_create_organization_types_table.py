"""create organization types table

Revision ID: 2e5b6f8c1d97
Revises: 9c3f7d21a8e4
Create Date: 2026-09-19 00:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '2e5b6f8c1d97'
down_revision: Union[str, Sequence[str], None] = '9c3f7d21a8e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'organization_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guid', sa.Uuid(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['usersreplica.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['usersreplica.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_organization_types_id'), 'organization_types', ['id'], unique=False)
    op.create_index(op.f('ix_organization_types_guid'), 'organization_types', ['guid'], unique=True)
    op.create_index(op.f('ix_organization_types_name'), 'organization_types', ['name'], unique=True)
    op.create_index(op.f('ix_organization_types_created_by'), 'organization_types', ['created_by'], unique=False)
    op.create_index(op.f('ix_organization_types_updated_by'), 'organization_types', ['updated_by'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_organization_types_updated_by'), table_name='organization_types')
    op.drop_index(op.f('ix_organization_types_created_by'), table_name='organization_types')
    op.drop_index(op.f('ix_organization_types_name'), table_name='organization_types')
    op.drop_index(op.f('ix_organization_types_guid'), table_name='organization_types')
    op.drop_index(op.f('ix_organization_types_id'), table_name='organization_types')
    op.drop_table('organization_types')
