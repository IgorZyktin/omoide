"""drop indexes for redundant uuids

Revision ID: dfdb436852da
Revises: 6974943d3a58
Create Date: 2024-10-31 10:28:07.534352+03:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = 'dfdb436852da'
down_revision: str | None = '6974943d3a58'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adding stuff."""
    op.drop_index(op.f('ix_items_owner_uuid'), table_name='items')
    op.drop_index(op.f('ix_items_parent_uuid'), table_name='items')


def downgrade() -> None:
    """Removing stuff."""
    op.create_index(op.f('ix_items_owner_uuid'), 'items', ['owner_uuid'], unique=False)
    op.create_index(op.f('ix_items_parent_uuid'), 'items', ['parent_uuid'], unique=False)
