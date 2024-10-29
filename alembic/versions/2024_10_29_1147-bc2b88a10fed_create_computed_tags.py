"""create computed tags

Revision ID: bc2b88a10fed
Revises: 8a834a50ca58
Create Date: 2024-10-29 11:47:54.574033+03:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'bc2b88a10fed'
down_revision: Union[str, None] = '8a834a50ca58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'computed_tags',
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('item_id'),
    )

    op.create_index('ix_computed_tags', 'computed_tags', ['tags'],
                    unique=False, postgresql_using='gin')
    op.create_index(op.f('ix_computed_tags_item_id'), 'computed_tags', ['item_id'],
                    unique=True)

    op.execute('GRANT ALL ON computed_tags TO omoide_app;')
    op.execute('GRANT ALL ON computed_tags TO omoide_worker;')
    op.execute('GRANT SELECT ON computed_tags TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.drop_index(op.f('ix_computed_tags_item_id'), table_name='computed_tags')
    op.drop_index('ix_computed_tags', table_name='computed_tags', postgresql_using='gin')
    op.drop_table('computed_tags')
