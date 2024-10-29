"""create item notes

Revision ID: 8a834a50ca58
Revises: 8080725c8d7a
Create Date: 2024-10-29 11:44:55.059587+03:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8a834a50ca58'
down_revision: Union[str, None] = '8080725c8d7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'item_notes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.CHAR(length=256), nullable=False),
        sa.Column('value', sa.CHAR(length=1024), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('item_id', 'key', name='item_notes_uc')
    )

    op.create_index(op.f('ix_item_notes_id'), 'item_notes', ['id'], unique=True)
    op.create_index(op.f('ix_item_notes_item_id'), 'item_notes', ['item_id'], unique=False)
    op.create_index(op.f('ix_item_notes_key'), 'item_notes', ['key'], unique=False)

    op.execute('GRANT ALL ON item_notes TO omoide_app;')
    op.execute('GRANT ALL ON item_notes TO omoide_worker;')
    op.execute('GRANT SELECT ON item_notes TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.drop_index(op.f('ix_item_notes_key'), table_name='item_notes')
    op.drop_index(op.f('ix_item_notes_item_id'), table_name='item_notes')
    op.drop_index(op.f('ix_item_notes_id'), table_name='item_notes')
    op.drop_table('item_notes')
