"""allow app to copy items

Revision ID: 8870dd74f3df
Revises: b86f52f0bf00
Create Date: 2024-11-16 20:57:03.499838+03:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = '8870dd74f3df'
down_revision: str | None = 'b86f52f0bf00'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adding stuff."""
    op.execute("""GRANT ALL ON SEQUENCE commands_copy_id_seq TO omoide_app;""")
    op.execute("""GRANT ALL ON SEQUENCE commands_copy_id_seq TO omoide_worker;""")


def downgrade() -> None:
    """Removing stuff."""
