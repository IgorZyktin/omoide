"""create serial_operations

Revision ID: 1b286a900ae0
Revises: ce3cd8b934bb
Create Date: 2024-10-29 11:34:54.982167+03:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '1b286a900ae0'
down_revision: str | None = 'ce3cd8b934bb'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'serial_operations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('worker_name', sa.String(length=256), nullable=True),
        sa.Column(
            'status',
            sa.Enum('created', 'processing', 'done', 'failed', name='serial_operation_status'),
            nullable=False,
        ),
        sa.Column('extras', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('log', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(op.f('ix_serial_operations_id'), 'serial_operations', ['id'], unique=True)

    op.execute('GRANT SELECT ON serial_operations TO omoide_app;')
    op.execute('GRANT ALL ON serial_operations TO omoide_worker;')
    op.execute('GRANT SELECT ON serial_operations TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.execute('REVOKE ALL PRIVILEGES ON serial_operations FROM omoide_app;')
    op.execute('REVOKE ALL PRIVILEGES ON serial_operations FROM omoide_worker;')
    op.execute('REVOKE ALL PRIVILEGES ON serial_operations FROM omoide_monitoring;')

    op.drop_index(op.f('ix_serial_operations_id'), table_name='serial_operations')
    op.drop_table('serial_operations')
