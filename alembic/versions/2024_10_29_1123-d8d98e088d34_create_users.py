"""create users

Revision ID: d8d98e088d34
Revises: 01c066d38f16
Create Date: 2024-10-29 11:23:36.348261+03:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'd8d98e088d34'
down_revision: str | None = '01c066d38f16'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.UUID(), nullable=False),
        sa.Column('role', sa.Integer(), nullable=False),
        sa.Column('login', sa.String(length=256), nullable=False),
        sa.Column('password', sa.String(length=1024), nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('auth_complexity', sa.Integer(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('registered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['role'], ['user_roles.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=True)
    op.create_index(op.f('ix_users_is_public'), 'users', ['is_public'], unique=False)
    op.create_index(op.f('ix_users_login'), 'users', ['login'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_uuid'), 'users', ['uuid'], unique=True)

    op.execute('GRANT ALL ON users TO omoide_app;')
    op.execute('GRANT SELECT ON users TO omoide_worker;')
    op.execute('GRANT SELECT ON users TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.execute('REVOKE ALL PRIVILEGES ON users FROM omoide_app;')
    op.execute('REVOKE ALL PRIVILEGES ON users FROM omoide_worker;')
    op.execute('REVOKE ALL PRIVILEGES ON users FROM omoide_monitoring;')

    op.drop_index(op.f('ix_users_uuid'), table_name='users')
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_login'), table_name='users')
    op.drop_index(op.f('ix_users_is_public'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
