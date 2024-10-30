"""create item statuses

Revision ID: 01c066d38f16
Revises: f9be6d5c70c5
Create Date: 2024-10-29 11:18:59.876821+03:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '01c066d38f16'
down_revision: Union[str, None] = 'f9be6d5c70c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'item_statuses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_item_statuses_id'), 'item_statuses', ['id'], unique=True)

    op.execute("INSERT INTO item_statuses VALUES (0, 'available');")
    op.execute("INSERT INTO item_statuses VALUES (1, 'created');")
    op.execute("INSERT INTO item_statuses VALUES (2, 'processing');")
    op.execute("INSERT INTO item_statuses VALUES (3, 'deleted');")
    op.execute("INSERT INTO item_statuses VALUES (4, 'error');")

    op.execute('GRANT SELECT ON item_statuses TO omoide_app;')
    op.execute('GRANT SELECT ON item_statuses TO omoide_worker;')
    op.execute('GRANT SELECT ON item_statuses TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.execute('REVOKE ALL PRIVILEGES ON item_statuses FROM omoide_app;')
    op.execute('REVOKE ALL PRIVILEGES ON item_statuses FROM omoide_worker;')
    op.execute('REVOKE ALL PRIVILEGES ON item_statuses FROM omoide_monitoring;')

    op.drop_index(op.f('ix_item_statuses_id'), table_name='item_statuses')
    op.drop_table('item_statuses')
