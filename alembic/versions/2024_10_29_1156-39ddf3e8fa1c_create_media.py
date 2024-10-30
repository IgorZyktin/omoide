"""create media

Revision ID: 39ddf3e8fa1c
Revises: 25f007832aec
Create Date: 2024-10-29 11:56:39.971200+03:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '39ddf3e8fa1c'
down_revision: Union[str, None] = '25f007832aec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'media',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('media_type', sa.Enum('content', 'preview', 'thumbnail', name='media_type'),
                  nullable=False),
        sa.Column('content', postgresql.BYTEA(), nullable=False),
        sa.Column('ext', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_media_created_at'), 'media', ['created_at'], unique=False)
    op.create_index(op.f('ix_media_id'), 'media', ['id'], unique=True)
    op.create_index(op.f('ix_media_item_id'), 'media', ['item_id'], unique=False)
    op.create_index(op.f('ix_media_owner_id'), 'media', ['owner_id'], unique=False)
    op.create_index(op.f('ix_media_processed_at'), 'media', ['processed_at'], unique=False)

    op.execute('GRANT ALL ON media TO omoide_app;')
    op.execute('GRANT ALL ON media TO omoide_worker;')
    op.execute('GRANT SELECT ON media TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.execute('REVOKE ALL PRIVILEGES ON media FROM omoide_app;')
    op.execute('REVOKE ALL PRIVILEGES ON media FROM omoide_worker;')
    op.execute('REVOKE ALL PRIVILEGES ON media FROM omoide_monitoring;')

    op.drop_index(op.f('ix_media_processed_at'), table_name='media')
    op.drop_index(op.f('ix_media_owner_id'), table_name='media')
    op.drop_index(op.f('ix_media_item_id'), table_name='media')
    op.drop_index(op.f('ix_media_id'), table_name='media')
    op.drop_index(op.f('ix_media_created_at'), table_name='media')
    op.drop_table('media')
