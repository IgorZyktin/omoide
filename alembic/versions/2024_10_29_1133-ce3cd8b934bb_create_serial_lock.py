"""create serial lock

Revision ID: ce3cd8b934bb
Revises: e65532acc2b2
Create Date: 2024-10-29 11:33:14.748437+03:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ce3cd8b934bb'
down_revision: Union[str, None] = 'e65532acc2b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'serial_lock',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('worker_name', sa.VARCHAR(length=256), nullable=True),
        sa.Column('last_update', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_serial_lock_id'), 'serial_lock', ['id'], unique=True)
    op.create_index(op.f('ix_serial_lock_last_update'),
                    'serial_lock', ['last_update'], unique=False)

    op.execute('GRANT SELECT ON serial_lock TO omoide_app;')
    op.execute('GRANT ALL ON serial_lock TO omoide_worker;')
    op.execute('GRANT SELECT ON serial_lock TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.drop_index(op.f('ix_serial_lock_last_update'), table_name='serial_lock')
    op.drop_index(op.f('ix_serial_lock_id'), table_name='serial_lock')
    op.drop_table('serial_lock')
