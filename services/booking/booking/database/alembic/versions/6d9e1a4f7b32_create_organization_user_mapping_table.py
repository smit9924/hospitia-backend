"""create organization user mapping table

Revision ID: 6d9e1a4f7b32
Revises: 4f8a2b6e9c05
Create Date: 2026-09-19 00:04:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '6d9e1a4f7b32'
down_revision: Union[str, Sequence[str], None] = '4f8a2b6e9c05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'organization_user_mapping',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guid', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['usersreplica.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['usersreplica.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['usersreplica.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'user_id', 'role', name='uq_org_user_mapping_org_user_role'),
    )
    op.create_index(op.f('ix_organization_user_mapping_id'), 'organization_user_mapping', ['id'], unique=False)
    op.create_index(op.f('ix_organization_user_mapping_guid'), 'organization_user_mapping', ['guid'], unique=True)
    op.create_index(op.f('ix_organization_user_mapping_organization_id'), 'organization_user_mapping', ['organization_id'], unique=False)
    op.create_index(op.f('ix_organization_user_mapping_user_id'), 'organization_user_mapping', ['user_id'], unique=False)
    op.create_index(op.f('ix_organization_user_mapping_role'), 'organization_user_mapping', ['role'], unique=False)
    op.create_index(op.f('ix_organization_user_mapping_is_active'), 'organization_user_mapping', ['is_active'], unique=False)
    op.create_index(op.f('ix_organization_user_mapping_created_by'), 'organization_user_mapping', ['created_by'], unique=False)
    op.create_index(op.f('ix_organization_user_mapping_updated_by'), 'organization_user_mapping', ['updated_by'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_organization_user_mapping_updated_by'), table_name='organization_user_mapping')
    op.drop_index(op.f('ix_organization_user_mapping_created_by'), table_name='organization_user_mapping')
    op.drop_index(op.f('ix_organization_user_mapping_is_active'), table_name='organization_user_mapping')
    op.drop_index(op.f('ix_organization_user_mapping_role'), table_name='organization_user_mapping')
    op.drop_index(op.f('ix_organization_user_mapping_user_id'), table_name='organization_user_mapping')
    op.drop_index(op.f('ix_organization_user_mapping_organization_id'), table_name='organization_user_mapping')
    op.drop_index(op.f('ix_organization_user_mapping_guid'), table_name='organization_user_mapping')
    op.drop_index(op.f('ix_organization_user_mapping_id'), table_name='organization_user_mapping')
    op.drop_table('organization_user_mapping')
