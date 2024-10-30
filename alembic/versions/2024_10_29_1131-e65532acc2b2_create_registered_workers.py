"""create registered workers

Revision ID: e65532acc2b2
Revises: 2bf410fe41c1
Create Date: 2024-10-29 11:31:25.956285+03:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'e65532acc2b2'
down_revision: str | None = '2bf410fe41c1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'registered_workers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('worker_name', sa.String(length=256), nullable=False),
        sa.Column('last_restart', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(op.f('ix_registered_workers_id'), 'registered_workers', ['id'], unique=True)
    op.create_index(
        op.f('ix_registered_workers_last_restart'),
        'registered_workers',
        ['last_restart'],
        unique=False,
    )
    op.create_index(
        op.f('ix_registered_workers_worker_name'),
        'registered_workers',
        ['worker_name'],
        unique=True,
    )

    op.execute('GRANT SELECT ON registered_workers TO omoide_app;')
    op.execute('GRANT ALL ON registered_workers TO omoide_worker;')
    op.execute('GRANT SELECT ON registered_workers TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.execute('REVOKE ALL PRIVILEGES ON registered_workers FROM omoide_app;')
    op.execute('REVOKE ALL PRIVILEGES ON registered_workers FROM omoide_worker;')
    op.execute('REVOKE ALL PRIVILEGES ON registered_workers FROM omoide_monitoring;')

    op.drop_index(op.f('ix_registered_workers_worker_name'), table_name='registered_workers')
    op.drop_index(op.f('ix_registered_workers_last_restart'), table_name='registered_workers')
    op.drop_index(op.f('ix_registered_workers_id'), table_name='registered_workers')
    op.drop_table('registered_workers')
