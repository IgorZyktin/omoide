"""fill redundant uuids for items

Revision ID: d8231390e04b
Revises: b637cad1a67c
Create Date: 2024-10-30 15:01:11.762804+03:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = 'd8231390e04b'
down_revision: str | None = 'b637cad1a67c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adding stuff."""
    op.execute("""
    UPDATE items i SET owner_uuid = (SELECT u.uuid FROM users u WHERE u.id = i.owner_id);
    """)

    op.execute("""
    UPDATE items i1 SET parent_uuid = (SELECT i2.uuid FROM items i2 WHERE i2.id = i1.parent_id)
    WHERE i1.parent_id IS NOT NULL;
    """)

    op.alter_column('items', 'owner_uuid', nullable=False)


def downgrade() -> None:
    """Removing stuff."""
