"""redundant uuids for items

Revision ID: b637cad1a67c
Revises: 39ddf3e8fa1c
Create Date: 2024-10-30 14:52:45.367168+03:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b637cad1a67c'
down_revision: Union[str, None] = '39ddf3e8fa1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adding stuff."""
    op.add_column('items', sa.Column('parent_uuid', sa.UUID(), nullable=True))
    op.add_column('items', sa.Column('owner_uuid', sa.UUID(), nullable=True))

    op.create_index(op.f('ix_items_owner_uuid'), 'items', ['owner_uuid'], unique=False)
    op.create_index(op.f('ix_items_parent_uuid'), 'items', ['parent_uuid'], unique=False)

    op.create_foreign_key('items_owner_uuid_fkey', 'items', 'users', ['owner_uuid'], ['uuid'])
    op.create_foreign_key('items_parent_uuid_fkey', 'items', 'items', ['parent_uuid'], ['uuid'])


def downgrade() -> None:
    """Removing stuff."""
    op.drop_index(op.f('ix_items_owner_uuid'), table_name='items')
    op.drop_index(op.f('ix_items_parent_uuid'), table_name='items')

    op.drop_constraint('items_owner_uuid_fkey', 'items')
    op.drop_constraint('items_parent_uuid_fkey', 'items')
