"""create organizations table

Revision ID: 4f8a2b6e9c05
Revises: 2e5b6f8c1d97
Create Date: 2026-09-19 00:03:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '4f8a2b6e9c05'
down_revision: Union[str, Sequence[str], None] = '2e5b6f8c1d97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guid', sa.Uuid(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column('organization_type_id', sa.Integer(), nullable=False),
        sa.Column('address_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['organization_type_id'], ['organization_types.id']),
        sa.ForeignKeyConstraint(['address_id'], ['addresses.id']),
        sa.ForeignKeyConstraint(['created_by'], ['usersreplica.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['usersreplica.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_guid'), 'organizations', ['guid'], unique=True)
    op.create_index(op.f('ix_organizations_name'), 'organizations', ['name'], unique=False)
    op.create_index(op.f('ix_organizations_organization_type_id'), 'organizations', ['organization_type_id'], unique=False)
    op.create_index(op.f('ix_organizations_address_id'), 'organizations', ['address_id'], unique=True)
    op.create_index(op.f('ix_organizations_is_active'), 'organizations', ['is_active'], unique=False)
    op.create_index(op.f('ix_organizations_created_by'), 'organizations', ['created_by'], unique=False)
    op.create_index(op.f('ix_organizations_updated_by'), 'organizations', ['updated_by'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_organizations_updated_by'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_created_by'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_is_active'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_address_id'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_organization_type_id'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_name'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_guid'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')
