"""more rights on serial operations

Revision ID: de66fcce311e
Revises: dfdb436852da
Create Date: 2024-10-31 13:21:06.126981+03:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = 'de66fcce311e'
down_revision: str | None = 'dfdb436852da'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adding stuff."""
    op.execute('GRANT INSERT ON serial_operations TO omoide_app;')


def downgrade() -> None:
    """Removing stuff."""
    op.execute('REVOKE INSERT ON serial_operations FROM omoide_app;')
