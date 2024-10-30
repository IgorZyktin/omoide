"""create known tags anon

Revision ID: 2bf410fe41c1
Revises: 91e06fe7de8d
Create Date: 2024-10-29 11:28:55.570421+03:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '2bf410fe41c1'
down_revision: str | None = '91e06fe7de8d'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'known_tags_anon',
        sa.Column('tag', sa.String(length=256), nullable=False),
        sa.Column('counter', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('tag'),
    )

    op.create_index(
        'ix_known_tags_anon',
        'known_tags_anon',
        ['tag'],
        unique=False,
        postgresql_ops={'tag': 'text_pattern_ops'},
    )
    op.create_index(op.f('ix_known_tags_anon_tag'), 'known_tags_anon', ['tag'], unique=True)

    op.execute('GRANT ALL ON known_tags_anon TO omoide_app;')
    op.execute('GRANT ALL ON known_tags_anon TO omoide_worker;')
    op.execute('GRANT SELECT ON known_tags_anon TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.execute('REVOKE ALL PRIVILEGES ON known_tags_anon FROM omoide_app;')
    op.execute('REVOKE ALL PRIVILEGES ON known_tags_anon FROM omoide_worker;')
    op.execute('REVOKE ALL PRIVILEGES ON known_tags_anon FROM omoide_monitoring;')

    op.drop_index(op.f('ix_known_tags_anon_tag'), table_name='known_tags_anon')
    op.drop_index(
        'ix_known_tags_anon',
        table_name='known_tags_anon',
        postgresql_ops={'tag': 'text_pattern_ops'},
    )
    op.drop_table('known_tags_anon')
