"""added problems

Revision ID: b86f52f0bf00
Revises: 75d07b1a7b39
Create Date: 2024-11-16 19:48:14.753286+03:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = 'b86f52f0bf00'
down_revision: str | None = '75d07b1a7b39'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'problems',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('extras', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_problems_id'), 'problems', ['id'], unique=True)
    op.create_index(op.f('ix_problems_created_at'), 'problems', ['created_at'])

    op.execute('GRANT ALL ON problems TO omoide_app;')
    op.execute('GRANT ALL ON problems TO omoide_worker;')
    op.execute('GRANT SELECT ON problems TO omoide_monitoring;')

    op.execute("""GRANT USAGE, SELECT ON SEQUENCE problems_id_seq TO omoide_app;""")
    op.execute("""GRANT USAGE, SELECT ON SEQUENCE problems_id_seq TO omoide_worker;""")
    op.execute("""GRANT SELECT ON SEQUENCE problems_id_seq TO omoide_monitoring;""")


def downgrade() -> None:
    """Removing stuff."""
    op.execute('REVOKE ALL PRIVILEGES ON problems FROM omoide_app;')
    op.execute('REVOKE ALL PRIVILEGES ON problems FROM omoide_worker;')
    op.execute('REVOKE ALL PRIVILEGES ON problems FROM omoide_monitoring;')

    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE problems_id_seq FROM omoide_app;""")
    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE problems_id_seq FROM omoide_worker;""")
    op.execute("""REVOKE SELECT ON SEQUENCE problems_id_seq FROM omoide_monitoring;""")

    op.drop_index(op.f('ix_problems_id'), table_name='problems')
    op.drop_index(op.f('ix_problems_created_at'), table_name='problems')
    op.drop_table('problems')
