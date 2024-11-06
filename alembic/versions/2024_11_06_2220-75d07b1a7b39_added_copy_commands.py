"""added copy commands

Revision ID: 75d07b1a7b39
Revises: 64ea36d4fac4
Create Date: 2024-11-06 22:20:47.553717+03:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '75d07b1a7b39'
down_revision: str | None = '64ea36d4fac4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'commands_copy',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column(
            'media_type',
            sa.Enum('content', 'preview', 'thumbnail', name='media_type'),
            nullable=False,
        ),
        sa.Column('ext', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_commands_copy_created_at'), 'commands_copy', ['created_at'], unique=False
    )
    op.create_index(op.f('ix_commands_copy_id'), 'commands_copy', ['id'], unique=False)
    op.create_index(op.f('ix_commands_copy_owner_id'), 'commands_copy', ['owner_id'], unique=False)

    op.execute('GRANT ALL ON commands_copy TO omoide_app;')
    op.execute('GRANT ALL ON commands_copy TO omoide_worker;')
    op.execute('GRANT SELECT ON commands_copy TO omoide_monitoring;')

    op.execute("""GRANT USAGE, SELECT ON SEQUENCE commands_copy_id_seq TO omoide_app;""")
    op.execute("""GRANT USAGE, SELECT ON SEQUENCE commands_copy_id_seq TO omoide_worker;""")
    op.execute("""GRANT SELECT ON SEQUENCE commands_copy_id_seq TO omoide_monitoring;""")


def downgrade() -> None:
    """Removing stuff."""
    op.execute('REVOKE ALL PRIVILEGES ON commands_copy FROM omoide_app;')
    op.execute('REVOKE ALL PRIVILEGES ON commands_copy FROM omoide_worker;')
    op.execute('REVOKE ALL PRIVILEGES ON commands_copy FROM omoide_monitoring;')

    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE commands_copy_id_seq FROM omoide_app;""")
    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE commands_copy_id_seq FROM omoide_worker;""")
    op.execute("""REVOKE SELECT ON SEQUENCE commands_copy_id_seq FROM omoide_monitoring;""")

    op.drop_index(op.f('ix_commands_copy_owner_id'), table_name='commands_copy')
    op.drop_index(op.f('ix_commands_copy_id'), table_name='commands_copy')
    op.drop_index(op.f('ix_commands_copy_created_at'), table_name='commands_copy')
    op.drop_table('commands_copy')
