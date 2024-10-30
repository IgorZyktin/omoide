"""sequence permissions

Revision ID: 6974943d3a58
Revises: d8231390e04b
Create Date: 2024-10-30 23:07:48.036857+03:00
"""

from typing import Sequence, Union

from alembic import op


revision: str = '6974943d3a58'
down_revision: Union[str, None] = 'd8231390e04b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adding stuff."""
    op.execute("""GRANT USAGE, SELECT ON SEQUENCE item_notes_id_seq TO omoide_app;""")
    op.execute("""GRANT USAGE, SELECT ON SEQUENCE items_id_seq TO omoide_app;""")
    op.execute("""GRANT USAGE, SELECT ON SEQUENCE media_id_seq TO omoide_app;""")
    op.execute("""GRANT USAGE, SELECT ON SEQUENCE registered_workers_id_seq TO omoide_app;""")
    op.execute("""GRANT USAGE, SELECT ON SEQUENCE serial_lock_id_seq TO omoide_app;""")
    op.execute("""GRANT USAGE, SELECT ON SEQUENCE serial_operations_id_seq TO omoide_app;""")
    op.execute("""GRANT USAGE, SELECT ON SEQUENCE users_id_seq TO omoide_app;""")

    op.execute("""GRANT USAGE, SELECT ON SEQUENCE item_notes_id_seq TO omoide_worker;""")
    op.execute("""GRANT USAGE, SELECT ON SEQUENCE items_id_seq TO omoide_worker;""")
    op.execute("""GRANT USAGE, SELECT ON SEQUENCE media_id_seq TO omoide_worker;""")
    op.execute("""GRANT USAGE, SELECT ON SEQUENCE registered_workers_id_seq TO omoide_worker;""")
    op.execute("""GRANT USAGE, SELECT ON SEQUENCE serial_lock_id_seq TO omoide_worker;""")
    op.execute("""GRANT USAGE, SELECT ON SEQUENCE serial_operations_id_seq TO omoide_worker;""")
    op.execute("""GRANT USAGE, SELECT ON SEQUENCE users_id_seq TO omoide_worker;""")

    op.execute("""GRANT SELECT ON SEQUENCE item_notes_id_seq TO omoide_monitoring;""")
    op.execute("""GRANT SELECT ON SEQUENCE items_id_seq TO omoide_monitoring;""")
    op.execute("""GRANT SELECT ON SEQUENCE media_id_seq TO omoide_monitoring;""")
    op.execute("""GRANT SELECT ON SEQUENCE registered_workers_id_seq TO omoide_monitoring;""")
    op.execute("""GRANT SELECT ON SEQUENCE serial_lock_id_seq TO omoide_monitoring;""")
    op.execute("""GRANT SELECT ON SEQUENCE serial_operations_id_seq TO omoide_monitoring;""")
    op.execute("""GRANT SELECT ON SEQUENCE users_id_seq TO omoide_monitoring;""")


def downgrade() -> None:
    """Removing stuff."""
    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE item_notes_id_seq TO omoide_app;""")
    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE items_id_seq TO omoide_app;""")
    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE media_id_seq TO omoide_app;""")
    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE registered_workers_id_seq TO omoide_app;""")
    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE serial_lock_id_seq TO omoide_app;""")
    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE serial_operations_id_seq TO omoide_app;""")
    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE users_id_seq TO omoide_app;""")

    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE item_notes_id_seq TO omoide_worker;""")
    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE items_id_seq TO omoide_worker;""")
    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE media_id_seq TO omoide_worker;""")
    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE registered_workers_id_seq TO omoide_worker;""")
    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE serial_lock_id_seq TO omoide_worker;""")
    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE serial_operations_id_seq TO omoide_worker;""")
    op.execute("""REVOKE USAGE, SELECT ON SEQUENCE users_id_seq TO omoide_worker;""")

    op.execute("""REVOKE SELECT ON SEQUENCE item_notes_id_seq TO omoide_monitoring;""")
    op.execute("""REVOKE SELECT ON SEQUENCE items_id_seq TO omoide_monitoring;""")
    op.execute("""REVOKE SELECT ON SEQUENCE media_id_seq TO omoide_monitoring;""")
    op.execute("""REVOKE SELECT ON SEQUENCE registered_workers_id_seq TO omoide_monitoring;""")
    op.execute("""REVOKE SELECT ON SEQUENCE serial_lock_id_seq TO omoide_monitoring;""")
    op.execute("""REVOKE SELECT ON SEQUENCE serial_operations_id_seq TO omoide_monitoring;""")
    op.execute("""REVOKE SELECT ON SEQUENCE users_id_seq TO omoide_monitoring;""")
