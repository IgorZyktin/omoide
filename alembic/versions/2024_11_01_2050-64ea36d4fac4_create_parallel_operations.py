"""create parallel_operations

Revision ID: 64ea36d4fac4
Revises: de66fcce311e
Create Date: 2024-11-01 20:50:00.206320+03:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '64ea36d4fac4'
down_revision: str | None = 'de66fcce311e'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'parallel_operations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('extras', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('log', sa.Text(), nullable=True),
        sa.Column('payload', postgresql.BYTEA(), nullable=False),
        sa.Column('processed_by', postgresql.ARRAY(sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_parallel_operations_id'), 'parallel_operations', ['id'], unique=True)
    op.create_index(
        op.f('ix_parallel_operations_status'), 'parallel_operations', ['status'], unique=False
    )
    op.create_index(
        'ix_processed_by',
        'parallel_operations',
        ['processed_by'],
        unique=False,
        postgresql_using='gin',
    )


def downgrade() -> None:
    """Removing stuff."""
    op.drop_index('ix_processed_by', table_name='parallel_operations', postgresql_using='gin')
    op.drop_index(op.f('ix_parallel_operations_status'), table_name='parallel_operations')
    op.drop_index(op.f('ix_parallel_operations_id'), table_name='parallel_operations')
    op.drop_table('parallel_operations')
