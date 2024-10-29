"""create md5 and crc32 signatures

Revision ID: 316d326d0690
Revises: 55564454e156
Create Date: 2024-10-29 11:41:04.695228+03:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '316d326d0690'
down_revision: Union[str, None] = '55564454e156'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'signatures_crc32',
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('signature', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('item_id')
    )

    op.create_index(op.f('ix_signatures_crc32_item_id'),
                    'signatures_crc32', ['item_id'], unique=True)
    op.create_index(op.f('ix_signatures_crc32_signature'),
                    'signatures_crc32', ['signature'], unique=False)

    op.execute('GRANT SELECT ON signatures_crc32 TO omoide_app;')
    op.execute('GRANT ALL ON signatures_crc32 TO omoide_worker;')
    op.execute('GRANT SELECT ON signatures_crc32 TO omoide_monitoring;')

    op.create_table(
        'signatures_md5',
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('signature', sa.CHAR(length=32), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('item_id')
    )

    op.create_index(op.f('ix_signatures_md5_item_id'),
                    'signatures_md5', ['item_id'], unique=True)
    op.create_index(op.f('ix_signatures_md5_signature'),
                    'signatures_md5', ['signature'], unique=False)

    op.execute('GRANT SELECT ON signatures_md5 TO omoide_app;')
    op.execute('GRANT ALL ON signatures_md5 TO omoide_worker;')
    op.execute('GRANT SELECT ON signatures_md5 TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.drop_index(op.f('ix_signatures_md5_signature'), table_name='signatures_md5')
    op.drop_index(op.f('ix_signatures_md5_item_id'), table_name='signatures_md5')
    op.drop_table('signatures_md5')

    op.drop_index(op.f('ix_signatures_crc32_signature'), table_name='signatures_crc32')
    op.drop_index(op.f('ix_signatures_crc32_item_id'), table_name='signatures_crc32')
    op.drop_table('signatures_crc32')
