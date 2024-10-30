"""create exif

Revision ID: 8080725c8d7a
Revises: 316d326d0690
Create Date: 2024-10-29 11:43:18.001048+03:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '8080725c8d7a'
down_revision: Union[str, None] = '316d326d0690'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'exif',
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('exif', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('item_id')
    )

    op.create_index(op.f('ix_exif_item_id'), 'exif', ['item_id'], unique=True)

    op.execute('GRANT ALL ON exif TO omoide_app;')
    op.execute('GRANT ALL ON exif TO omoide_worker;')
    op.execute('GRANT SELECT ON exif TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.execute('REVOKE ALL PRIVILEGES ON exif FROM omoide_app;')
    op.execute('REVOKE ALL PRIVILEGES ON exif FROM omoide_worker;')
    op.execute('REVOKE ALL PRIVILEGES ON exif FROM omoide_monitoring;')

    op.drop_index(op.f('ix_exif_item_id'), table_name='exif')
    op.drop_table('exif')
