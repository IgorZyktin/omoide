"""Added parallel command queue

Revision ID: 84e7c23cac48
Revises: 8ca57ddc101c
Create Date: 2026-06-18 22:42:38.241036+03:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '84e7c23cac48'
down_revision: str | None = '8ca57ddc101c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'command_queue_parallel',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('requested_by', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('extras', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('log', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_command_queue_parallel_id'), 'command_queue_parallel', ['id'], unique=True
    )
    op.create_index(
        op.f('ix_command_queue_parallel_name'), 'command_queue_parallel', ['name'], unique=False
    )

    op.execute('GRANT ALL ON command_queue_parallel TO omoide_app;')
    op.execute('GRANT ALL ON command_queue_parallel TO omoide_worker;')
    op.execute('GRANT SELECT ON command_queue_parallel TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.execute('REVOKE ALL PRIVILEGES ON command_queue_parallel FROM omoide_app;')
    op.execute('REVOKE ALL PRIVILEGES ON command_queue_parallel FROM omoide_worker;')
    op.execute('REVOKE ALL PRIVILEGES ON command_queue_parallel FROM omoide_monitoring;')

    op.drop_index(op.f('ix_command_queue_parallel_id'), table_name='command_queue_parallel')
    op.drop_index(op.f('ix_command_queue_parallel_name'), table_name='command_queue_parallel')
    op.drop_table('command_queue_parallel')
