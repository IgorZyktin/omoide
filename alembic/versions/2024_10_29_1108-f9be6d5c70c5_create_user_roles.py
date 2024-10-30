"""create user roles

Revision ID: f9be6d5c70c5
Revises: 3cd33ce04e6c
Create Date: 2024-10-29 11:08:53.871977+03:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'f9be6d5c70c5'
down_revision: str | None = '3cd33ce04e6c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'user_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_user_roles_id'), 'user_roles', ['id'], unique=True)

    op.execute("INSERT INTO user_roles VALUES (0, 'user');")
    op.execute("INSERT INTO user_roles VALUES (1, 'anon');")
    op.execute("INSERT INTO user_roles VALUES (2, 'admin');")

    op.execute('GRANT SELECT ON user_roles TO omoide_app;')
    op.execute('GRANT SELECT ON user_roles TO omoide_worker;')
    op.execute('GRANT SELECT ON user_roles TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.execute('REVOKE ALL PRIVILEGES ON user_roles FROM omoide_app;')
    op.execute('REVOKE ALL PRIVILEGES ON user_roles FROM omoide_worker;')
    op.execute('REVOKE ALL PRIVILEGES ON user_roles FROM omoide_monitoring;')

    op.drop_index(op.f('ix_user_roles_id'), table_name='user_roles')
    op.drop_table('user_roles')
