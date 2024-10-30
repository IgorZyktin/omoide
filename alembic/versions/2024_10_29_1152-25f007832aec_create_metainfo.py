"""create metainfo

Revision ID: 25f007832aec
Revises: bc2b88a10fed
Create Date: 2024-10-29 11:52:51.766110+03:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '25f007832aec'
down_revision: str | None = 'bc2b88a10fed'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'item_metainfo',
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_time', sa.DateTime(), nullable=True),
        sa.Column('content_type', sa.String(length=64), nullable=True),
        sa.Column('content_size', sa.Integer(), nullable=True),
        sa.Column('preview_size', sa.Integer(), nullable=True),
        sa.Column('thumbnail_size', sa.Integer(), nullable=True),
        sa.Column('content_width', sa.Integer(), nullable=True),
        sa.Column('content_height', sa.Integer(), nullable=True),
        sa.Column('preview_width', sa.Integer(), nullable=True),
        sa.Column('preview_height', sa.Integer(), nullable=True),
        sa.Column('thumbnail_width', sa.Integer(), nullable=True),
        sa.Column('thumbnail_height', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('item_id'),
    )

    op.create_index(op.f('ix_item_metainfo_item_id'), 'item_metainfo', ['item_id'], unique=True)

    op.execute('GRANT ALL ON item_metainfo TO omoide_app;')
    op.execute('GRANT ALL ON item_metainfo TO omoide_worker;')
    op.execute('GRANT SELECT ON item_metainfo TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.execute('REVOKE ALL PRIVILEGES ON item_metainfo FROM omoide_app;')
    op.execute('REVOKE ALL PRIVILEGES ON item_metainfo FROM omoide_worker;')
    op.execute('REVOKE ALL PRIVILEGES ON item_metainfo FROM omoide_monitoring;')

    op.drop_index(op.f('ix_item_metainfo_item_id'), table_name='item_metainfo')
    op.drop_table('item_metainfo')
