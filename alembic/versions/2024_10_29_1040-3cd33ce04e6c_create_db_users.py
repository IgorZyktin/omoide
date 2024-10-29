"""create db users

Revision ID: 3cd33ce04e6c
Revises:
Create Date: 2024-10-29 10:40:14.100524+03:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = '3cd33ce04e6c'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adding stuff."""
    # NOTE: Do not forget to change passwords later!
    op.execute("CREATE ROLE omoide_app WITH LOGIN PASSWORD 'app-password1234';")
    op.execute("CREATE ROLE omoide_worker WITH LOGIN PASSWORD 'worker-password1234';")
    op.execute("CREATE ROLE omoide_monitoring WITH LOGIN PASSWORD 'monitoring-password1234';")


def downgrade() -> None:
    """Removing stuff."""
    op.execute('DROP ROLE omoide_app;')
    op.execute('DROP ROLE omoide_worker;')
    op.execute('DROP ROLE omoide_monitoring;')
