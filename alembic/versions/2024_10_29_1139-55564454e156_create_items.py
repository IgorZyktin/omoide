"""create items

Revision ID: 55564454e156
Revises: 1b286a900ae0
Create Date: 2024-10-29 11:39:01.201305+03:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '55564454e156'
down_revision: Union[str, None] = '1b286a900ae0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.UUID(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Integer(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('is_collection', sa.Boolean(), nullable=False),
        sa.Column('content_ext', sa.String(length=64), nullable=True),
        sa.Column('preview_ext', sa.String(length=64), nullable=True),
        sa.Column('thumbnail_ext', sa.String(length=64), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column('permissions', postgresql.ARRAY(sa.Integer), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['status'], ['item_statuses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_items_id'), 'items', ['id'], unique=True)
    op.create_index(op.f('ix_items_owner_id'), 'items', ['owner_id'], unique=False)
    op.create_index(op.f('ix_items_parent_id'), 'items', ['parent_id'], unique=False)
    op.create_index('ix_items_permissions', 'items', ['permissions'],
                    unique=False, postgresql_using='gin')
    op.create_index(op.f('ix_items_status'), 'items', ['status'], unique=False)
    op.create_index('ix_items_tags', 'items', ['tags'], unique=False, postgresql_using='gin')
    op.create_index(op.f('ix_items_uuid'), 'items', ['uuid'], unique=True)

    op.execute('GRANT ALL ON items TO omoide_app;')
    op.execute('GRANT ALL ON items TO omoide_worker;')
    op.execute('GRANT SELECT ON items TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.execute('REVOKE ALL PRIVILEGES ON items FROM omoide_app;')
    op.execute('REVOKE ALL PRIVILEGES ON items FROM omoide_worker;')
    op.execute('REVOKE ALL PRIVILEGES ON items FROM omoide_monitoring;')

    op.drop_index(op.f('ix_items_uuid'), table_name='items')
    op.drop_index('ix_items_tags', table_name='items', postgresql_using='gin')
    op.drop_index(op.f('ix_items_status'), table_name='items')
    op.drop_index('ix_items_permissions', table_name='items', postgresql_using='gin')
    op.drop_index(op.f('ix_items_parent_id'), table_name='items')
    op.drop_index(op.f('ix_items_owner_id'), table_name='items')
    op.drop_index(op.f('ix_items_id'), table_name='items')
    op.drop_table('items')
