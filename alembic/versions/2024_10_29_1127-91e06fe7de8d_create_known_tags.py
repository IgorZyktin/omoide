"""create known tags

Revision ID: 91e06fe7de8d
Revises: d8d98e088d34
Create Date: 2024-10-29 11:27:21.775397+03:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '91e06fe7de8d'
down_revision: Union[str, None] = 'd8d98e088d34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adding stuff."""
    op.create_table(
        'known_tags',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tag', sa.String(length=256), nullable=False),
        sa.Column('counter', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'tag')
    )

    op.create_index('ix_known_tags', 'known_tags', ['tag'],
                    unique=False, postgresql_ops={'tag': 'text_pattern_ops'})
    op.create_index(op.f('ix_known_tags_tag'), 'known_tags', ['tag'], unique=False)
    op.create_index(op.f('ix_known_tags_user_id'), 'known_tags', ['user_id'], unique=True)

    op.execute('GRANT ALL ON known_tags TO omoide_app;')
    op.execute('GRANT ALL ON known_tags TO omoide_worker;')
    op.execute('GRANT SELECT ON known_tags TO omoide_monitoring;')


def downgrade() -> None:
    """Removing stuff."""
    op.execute('REVOKE ALL PRIVILEGES ON known_tags FROM omoide_app;')
    op.execute('REVOKE ALL PRIVILEGES ON known_tags FROM omoide_worker;')
    op.execute('REVOKE ALL PRIVILEGES ON known_tags FROM omoide_monitoring;')

    op.drop_index(op.f('ix_known_tags_user_id'), table_name='known_tags')
    op.drop_index(op.f('ix_known_tags_tag'), table_name='known_tags')
    op.drop_index('ix_known_tags', table_name='known_tags',
                  postgresql_ops={'tag': 'text_pattern_ops'})
    op.drop_table('known_tags')
