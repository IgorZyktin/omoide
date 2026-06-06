"""Shared fixtures for integration tests.

These tests require a real PostgreSQL instance. The connection URL MUST be
provided via the ``OMOIDE_TEST_DB_URL`` env var, e.g.::

    export OMOIDE_TEST_DB_URL="postgresql+psycopg2://omoide:omoide@localhost:5432/omoide_test"

The DB pointed to is treated as disposable: every test truncates all tables
and unlinks every Postgres large object on teardown. Never point this at
production data.

The integration fixtures are SYNC because the workers (converter/downloader)
use sync SQLAlchemy. Async fixtures for use-case tests will live alongside
when those tests are written.
"""

from collections.abc import Iterator
import contextlib
from datetime import UTC
from datetime import datetime
import os
from pathlib import Path
from typing import Any
import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import Engine

from omoide import const
from omoide.database import db_models
from omoide.infra.interfaces.abs_metrics_collector import Metric

_TRUNCATE_TABLES = (
    'queue_input_media',
    'queue_output_media',
    'item_notes',
    'item_metainfo',
    'exif',
    'signatures_md5',
    'signatures_crc32',
    'media',
    'commands_copy',
    'computed_tags',
    'known_tags',
    'known_tags_anon',
    'serial_operations',
    'serial_lock',
    'parallel_operations',
    'problems',
    'items',
    'users',
)


@pytest.fixture(scope='session')
def test_db_url() -> str:
    """Return the integration test DB URL or skip the session.

    Skips loudly with a clear message so the user knows integration tests
    were not exercised (per CLAUDE.md §2).
    """
    url = os.environ.get('OMOIDE_TEST_DB_URL')
    if not url:
        pytest.skip(
            'OMOIDE_TEST_DB_URL is not set; integration tests skipped. '
            'Point it at a disposable PostgreSQL database, e.g. '
            'postgresql+psycopg2://omoide:omoide@localhost:5432/omoide_test',
            allow_module_level=True,
        )
    return url


@pytest.fixture(scope='session')
def _schema_engine(test_db_url: str) -> Iterator[Engine]:
    """Create the schema once per session."""
    engine = sa.create_engine(test_db_url, future=True, pool_pre_ping=True)

    # Self-referential FKs (e.g. items.parent_uuid → items.uuid) live in the
    # CREATE TABLE statement while their target's unique index is emitted as
    # a separate CREATE UNIQUE INDEX afterwards — Postgres rejects the FK
    # for lack of a unique constraint. Re-emit those FKs as post-create
    # ALTERs. Production uses Alembic migrations which already split DDL
    # this way, so this is test-only schema-bootstrap glue.
    for table in db_models.Base.metadata.tables.values():
        for fk in table.foreign_keys:
            if fk.column.table is table:
                fk.constraint.use_alter = True

    db_models.Base.metadata.create_all(engine, checkfirst=True)

    role_rows = [
        {'id': 0, 'description': 'user'},
        {'id': 1, 'description': 'anon'},
        {'id': 2, 'description': 'admin'},
    ]
    status_rows = [
        {'id': 0, 'description': 'available'},
        {'id': 1, 'description': 'created'},
        {'id': 2, 'description': 'processing'},
        {'id': 3, 'description': 'deleted'},
        {'id': 4, 'description': 'error'},
    ]
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                'INSERT INTO user_roles (id, description) VALUES (:id, :description) '
                'ON CONFLICT (id) DO NOTHING'
            ),
            role_rows,
        )
        conn.execute(
            sa.text(
                'INSERT INTO item_statuses (id, description) VALUES (:id, :description) '
                'ON CONFLICT (id) DO NOTHING'
            ),
            status_rows,
        )

    yield engine
    engine.dispose()


def _truncate_all(engine: Engine) -> None:
    tables = ', '.join(_TRUNCATE_TABLES)
    with engine.begin() as conn:
        conn.execute(sa.text(f'TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE'))


def _unlink_all_large_objects(engine: Engine) -> None:
    """Drop every large object in the test DB.

    Large objects are not covered by TRUNCATE — they live in
    ``pg_largeobject`` and must be unlinked explicitly to avoid leaking
    storage between tests.
    """
    with engine.connect() as conn:
        oids = [row[0] for row in conn.execute(sa.text('SELECT oid FROM pg_largeobject_metadata'))]
    if not oids:
        return
    raw = engine.raw_connection()
    try:
        for oid in oids:
            with contextlib.suppress(Exception):
                raw.lobject(oid).unlink()
        raw.commit()
    finally:
        raw.close()


@pytest.fixture
def engine(_schema_engine: Engine) -> Iterator[Engine]:
    """Provide a sync engine bound to a clean DB.

    Wipes mutable tables and unlinks any orphan large objects before and
    after each test. Cleaning both ends means a crashing test cannot leak
    state into the next one.
    """
    _truncate_all(_schema_engine)
    _unlink_all_large_objects(_schema_engine)
    yield _schema_engine
    _truncate_all(_schema_engine)
    _unlink_all_large_objects(_schema_engine)


# Factories --------------------------------------------------------------


@pytest.fixture
def make_user(engine: Engine):
    """Insert a user into the test DB and return ``(id, uuid)``."""

    def _factory(**overrides: Any) -> tuple[int, uuid.UUID]:
        user_uuid = overrides.pop('uuid', uuid.uuid4())
        values: dict[str, Any] = {
            'uuid': user_uuid,
            'role': 0,
            'login': f'login-{user_uuid}',
            'password': 'x',
            'name': overrides.pop('name', 'test-user'),
            'auth_complexity': 1,
            'is_public': False,
            'registered_at': datetime.now(UTC),
            'last_login': None,
        }
        values.update(overrides)
        with engine.begin() as conn:
            result = conn.execute(
                sa.insert(db_models.User).values(**values).returning(db_models.User.id)
            )
            user_id = result.scalar_one()
        return int(user_id), user_uuid

    return _factory


@pytest.fixture
def make_item(engine: Engine, make_user):
    """Insert an item into the test DB and return ``(id, uuid, owner_uuid)``."""

    def _factory(**overrides: Any) -> tuple[int, uuid.UUID, uuid.UUID]:
        if 'owner_uuid' in overrides and 'owner_id' in overrides:
            owner_id = overrides.pop('owner_id')
            owner_uuid = overrides.pop('owner_uuid')
        else:
            owner_id, owner_uuid = make_user()
            overrides.pop('owner_id', None)
            overrides.pop('owner_uuid', None)

        item_uuid = overrides.pop('uuid', uuid.uuid4())
        values: dict[str, Any] = {
            'uuid': item_uuid,
            'parent_id': None,
            'parent_uuid': None,
            'owner_id': owner_id,
            'owner_uuid': owner_uuid,
            'status': 1,  # CREATED
            'number': 1,
            'name': overrides.pop('name', 'test-item'),
            'is_collection': False,
            'content_ext': None,
            'preview_ext': None,
            'thumbnail_ext': None,
            'tags': [],
            'permissions': [],
        }
        values.update(overrides)
        with engine.begin() as conn:
            result = conn.execute(
                sa.insert(db_models.Item).values(**values).returning(db_models.Item.id)
            )
            item_id = result.scalar_one()
        return int(item_id), item_uuid, owner_uuid

    return _factory


@pytest.fixture
def insert_input_media(engine: Engine):
    """Insert a row directly into ``queue_input_media``."""

    def _factory(
        *,
        user_uuid: uuid.UUID,
        item_uuid: uuid.UUID,
        content: bytes = b'',
        content_type: str = 'image/jpeg',
        ext: str = 'jpg',
        oid: int | None = None,
        extras: dict[str, Any] | None = None,
        lock: str | None = None,
        error: str | None = None,
    ) -> int:
        merged_extras: dict[str, Any] = {'extract_exif': False, 'oid': oid}
        if extras:
            merged_extras.update(extras)
        with engine.begin() as conn:
            result = conn.execute(
                sa.insert(db_models.QueueInputMedia)
                .values(
                    user_uuid=user_uuid,
                    item_uuid=item_uuid,
                    created_at=datetime.now(UTC),
                    lock=lock,
                    ext=ext,
                    content_type=content_type,
                    extras=merged_extras,
                    error=error,
                    content=content,
                )
                .returning(db_models.QueueInputMedia.id)
            )
            return int(result.scalar_one())

    return _factory


# Misc helpers -----------------------------------------------------------


@pytest.fixture
def large_payload() -> bytes:
    """Return a payload that exceeds ``LARGE_OBJECT_SIZE``."""
    return b'A' * (const.LARGE_OBJECT_SIZE + 1)


class FakeMetricsCollector:
    """In-memory metrics collector for worker tests.

    Avoids the global ``prometheus_client`` registry (which forbids
    duplicate timeseries between fixture instantiations) and avoids
    starting a real HTTP server.
    """

    def __init__(self) -> None:
        self._values: dict[int, float] = {}

    def increment(self, metric: Metric, value: float = 1.0) -> None:
        self._values[metric.id] = self._values.get(metric.id, 0.0) + value

    def get_value(self, metric: Metric) -> float:
        return self._values.get(metric.id, 0.0)


@pytest.fixture
def metrics_collector() -> FakeMetricsCollector:
    """Provide a no-op metrics collector."""
    return FakeMetricsCollector()


@pytest.fixture
def converter_temp_folder(tmp_path: Path) -> Path:
    """Provide a temp folder for the converter worker."""
    folder = tmp_path / 'converter'
    folder.mkdir()
    return folder
