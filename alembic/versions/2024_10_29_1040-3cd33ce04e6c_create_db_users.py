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
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT * FROM pg_roles WHERE rolname='omoide_app') THEN
            CREATE ROLE omoide_app WITH LOGIN Password 'app-password1234';
        END IF;
    END $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT * FROM pg_roles WHERE rolname='omoide_worker') THEN
            CREATE ROLE omoide_worker WITH LOGIN Password 'worker-password1234';
        END IF;
    END $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT * FROM pg_roles WHERE rolname='omoide_monitoring') THEN
            CREATE ROLE omoide_monitoring WITH LOGIN Password 'monitoring-password1234';
        END IF;
    END $$;
    """)


def downgrade() -> None:
    """Removing stuff."""
    op.execute('DROP ROLE IF EXISTS omoide_app;')
    op.execute('DROP ROLE IF EXISTS omoide_worker;')
    op.execute('DROP ROLE IF EXISTS omoide_monitoring;')
