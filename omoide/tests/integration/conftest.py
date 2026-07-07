"""Shared fixtures for integration tests.

These tests require a real PostgreSQL instance. The connection URL MUST be
provided via the ``OMOIDE_TEST_DB_URL`` env var, e.g.::

    export OMOIDE_TEST_DB_URL="postgresql+psycopg2://omoide:omoide@localhost:5432/omoide_test"

The DB pointed to is treated as disposable: every test truncates all tables
and unlinks every Postgres large object on teardown. Never point this at
production data.

Two parallel fixture stacks live here:

* SYNC — engine/make_user/make_item/etc. Used by the worker tests
  (converter, downloader) which run on sync SQLAlchemy.
* ASYNC — async_database + individual repo fixtures (users_repo,
  items_repo, ...)/make_user_model/make_item_model. Used by use-case
  tests which exercise the production async stack.

Both stacks point at the same physical database. The function-scoped
``engine`` fixture truncates between tests, so the async stack sees a
clean DB on every test as long as it depends on ``engine`` (directly or
transitively through ``async_database``).
"""

from collections.abc import AsyncIterator
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
from omoide import models
from omoide.database import db_models
from omoide.database.implementations import impl_sqlalchemy
from omoide.infra.interfaces.abs_metrics_collector import Metric

_TRUNCATE_TABLES = (
    'item_notes',
    'item_metainfo',
    'exif',
    'signatures_md5',
    'signatures_crc32',
    'computed_tags',
    'known_tags',
    'known_tags_anon',
    'serial_operations',
    'serial_lock',
    'command_queue_parallel',
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
    return b'A' * (const.MEGABYTE + 1)


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


# Async fixtures ---------------------------------------------------------
#
# Use-cases run on async SQLAlchemy in production. These fixtures wire up
# a real ``SqlalchemyDatabase`` plus all repos against the same physical
# test DB that the sync fixtures use. Isolation between tests still comes
# from the function-scoped ``engine`` fixture's truncate cycle — depend
# on it (directly or transitively) so the DB is clean.


def _to_async_url(url: str) -> str:
    """Convert a sync-driver Postgres URL to the asyncpg driver.

    The test env var historically points at psycopg2 for the sync workers.
    Async fixtures need the same DB through asyncpg.
    """
    for prefix in ('postgresql+psycopg2://', 'postgresql+psycopg://', 'postgresql://'):
        if url.startswith(prefix):
            return 'postgresql+asyncpg://' + url[len(prefix) :]
    return url


@pytest.fixture(scope='session')
def async_db_url(test_db_url: str) -> str:
    """Return the async (asyncpg) variant of the test DB URL."""
    return _to_async_url(test_db_url)


@pytest.fixture
async def async_database(
    async_db_url: str, _schema_engine: Engine, engine: Engine
) -> AsyncIterator[impl_sqlalchemy.SqlalchemyDatabase]:
    """Async database bound to the test DB.

    Function-scoped so it shares the per-test event loop pytest-asyncio
    provides (the default ``asyncio_default_fixture_loop_scope`` is
    ``function``). Engine creation is cheap; the connection pool is lazy
    so this only opens a real socket on first transaction.

    Depending on ``_schema_engine`` guarantees the schema has been
    bootstrapped before any async test reaches for it. Depending on
    ``engine`` makes the per-test truncate cycle apply to any async test
    that uses ``async_database`` (directly or transitively through one of
    the repo fixtures below).
    """
    _ = _schema_engine  # ordering dependency only
    _ = engine  # truncates between tests
    database = impl_sqlalchemy.SqlalchemyDatabase(async_db_url)
    await database.connect()
    try:
        yield database
    finally:
        await database.disconnect()


@pytest.fixture
def users_repo() -> impl_sqlalchemy.UsersRepo:
    """Provide a ``UsersRepo`` for use-case tests."""
    return impl_sqlalchemy.UsersRepo()


@pytest.fixture
def items_repo() -> impl_sqlalchemy.ItemsRepo:
    """Provide an ``ItemsRepo`` for use-case tests."""
    return impl_sqlalchemy.ItemsRepo()


@pytest.fixture
def meta_repo() -> impl_sqlalchemy.MetaRepo:
    """Provide a ``MetaRepo`` for use-case tests."""
    return impl_sqlalchemy.MetaRepo()


@pytest.fixture
def misc_repo() -> impl_sqlalchemy.MiscRepo:
    """Provide a ``MiscRepo`` for use-case tests."""
    return impl_sqlalchemy.MiscRepo()


@pytest.fixture
def tags_repo() -> impl_sqlalchemy.TagsRepo:
    """Provide a ``TagsRepo`` for use-case tests."""
    return impl_sqlalchemy.TagsRepo()


@pytest.fixture
def signatures_repo() -> impl_sqlalchemy.SignaturesRepo:
    """Provide a ``SignaturesRepo`` for use-case tests."""
    return impl_sqlalchemy.SignaturesRepo()


@pytest.fixture
def commands_repo() -> impl_sqlalchemy.CommandsRepo:
    """Provide a ``CommandsRepo`` for use-case tests."""
    return impl_sqlalchemy.CommandsRepo()


@pytest.fixture
def make_user_model(
    make_user,
    async_database: impl_sqlalchemy.SqlalchemyDatabase,
    users_repo: impl_sqlalchemy.UsersRepo,
):
    """Create a user row and return the domain ``models.User``.

    Accepts the same overrides as ``make_user`` plus reads the row back
    through ``UsersRepo`` so tests get a model identical to one the
    use-case would have produced.
    """

    async def _factory(**overrides: Any) -> models.User:
        user_id, _user_uuid = make_user(**overrides)
        async with async_database.transaction() as conn:
            return await users_repo.get_by_id(conn, user_id)

    return _factory


@pytest.fixture
def make_item_model(
    make_item,
    async_database: impl_sqlalchemy.SqlalchemyDatabase,
    items_repo: impl_sqlalchemy.ItemsRepo,
):
    """Create an item row and return the domain ``models.Item``.

    Accepts the same overrides as ``make_item``. Reads back via
    ``ItemsRepo`` so tests work with the same shape the use-case sees.
    """

    async def _factory(**overrides: Any) -> models.Item:
        item_id, _item_uuid, _owner_uuid = make_item(**overrides)
        async with async_database.transaction() as conn:
            return await items_repo.get_by_id(conn, item_id)

    return _factory


@pytest.fixture
def make_metainfo(engine: Engine):
    """Insert a metainfo row for the given item id and return its model.

    Most item flows expect a row in ``item_metainfo`` to exist; otherwise
    ``meta.soft_delete`` no-ops and ``meta.get_by_item`` raises.
    """

    def _factory(item_id: int, **overrides: Any) -> models.Metainfo:
        now = datetime.now(UTC)
        values: dict[str, Any] = {
            'item_id': item_id,
            'created_at': now,
            'updated_at': now,
            'deleted_at': None,
            'user_time': None,
            'content_type': overrides.pop('content_type', 'image/jpeg'),
            'content_size': None,
            'preview_size': None,
            'thumbnail_size': None,
            'content_width': None,
            'content_height': None,
            'preview_width': None,
            'preview_height': None,
            'thumbnail_width': None,
            'thumbnail_height': None,
        }
        values.update(overrides)
        with engine.begin() as conn:
            conn.execute(sa.insert(db_models.Metainfo).values(**values))
        return models.Metainfo(
            item_id=item_id,
            created_at=values['created_at'],
            updated_at=values['updated_at'],
            deleted_at=values['deleted_at'],
            user_time=values['user_time'],
            content_type=values['content_type'],
            content_size=values['content_size'],
            preview_size=values['preview_size'],
            thumbnail_size=values['thumbnail_size'],
            content_width=values['content_width'],
            content_height=values['content_height'],
            preview_width=values['preview_width'],
            preview_height=values['preview_height'],
            thumbnail_width=values['thumbnail_width'],
            thumbnail_height=values['thumbnail_height'],
        )

    return _factory


@pytest.fixture
def set_computed_tags(engine: Engine):
    """Upsert ``computed_tags`` for an item.

    The delete use-case reads computed_tags BEFORE clearing them and uses
    the snapshot to decrement ``known_tags``. Tests that care about
    that branch need pre-seeded data.
    """

    def _factory(item_id: int, tags: set[str]) -> None:
        with engine.begin() as conn:
            conn.execute(
                sa.delete(db_models.ComputedTags).where(db_models.ComputedTags.item_id == item_id)
            )
            conn.execute(
                sa.insert(db_models.ComputedTags).values(item_id=item_id, tags=tuple(sorted(tags)))
            )

    return _factory


@pytest.fixture
def set_known_tags_user(engine: Engine):
    """Upsert per-user ``known_tags`` counters."""

    def _factory(user_id: int, tags: dict[str, int]) -> None:
        if not tags:
            return
        with engine.begin() as conn:
            conn.execute(
                sa.delete(db_models.KnownTags).where(
                    db_models.KnownTags.user_id == user_id,
                    db_models.KnownTags.tag.in_(tags),
                )
            )
            conn.execute(
                sa.insert(db_models.KnownTags),
                [
                    {'user_id': user_id, 'tag': tag, 'counter': counter}
                    for tag, counter in tags.items()
                ],
            )

    return _factory


@pytest.fixture
def set_known_tags_anon(engine: Engine):
    """Upsert anon ``known_tags`` counters."""

    def _factory(tags: dict[str, int]) -> None:
        if not tags:
            return
        with engine.begin() as conn:
            conn.execute(
                sa.delete(db_models.KnownTagsAnon).where(db_models.KnownTagsAnon.tag.in_(tags))
            )
            conn.execute(
                sa.insert(db_models.KnownTagsAnon),
                [{'tag': tag, 'counter': counter} for tag, counter in tags.items()],
            )

    return _factory
