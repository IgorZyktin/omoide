"""Tests.
"""
import asyncio
import os
from unittest.mock import patch
from urllib.parse import urlsplit
from uuid import UUID

import pytest
import pytest_asyncio
from databases import Database

from omoide import infra
from omoide.domain import auth
from omoide.domain import common
from omoide.storage.repositories import asyncpg
from omoide.storage.repositories.asyncpg.rp_test import RepositoryForTests
from omoide.tests import constants


def safely_get_test_database(url: str | None = None) -> str:
    """Get url from env variables."""
    url = url or os.environ.get(constants.DB_ENV_VARIABLE)

    if url is None:
        msg = ('To perform functional tests you have '
               f'to set {constants.DB_ENV_VARIABLE} env variable')
        raise RuntimeError(msg)

    if constants.TEST_DB_NAME not in url.lower():
        parts = urlsplit(url, allow_fragments=True)
        safe_url = f'{parts.scheme}://<username>:<password>{parts.path}'
        if parts.query:
            safe_url += f'?{parts.query}'
        msg = ("Are you sure that you're using test database? "
               f"Expected something with {constants.TEST_DB_NAME!r}, "
               f"got: {safe_url}")
        raise RuntimeError(msg)

    return url


def test_safely_get_test_database_good():
    """Must pass."""
    # arrange
    url = 'postgresql://user:password@127.0.0.1:5432/omoide_test'

    # act
    result = safely_get_test_database(url)

    # assert
    assert result is not None


def test_safely_get_test_database_no_env():
    """Must find out that env is not set."""
    # act
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError, match='env variable'):
            safely_get_test_database()


def test_safely_get_test_database_incorrect_db():
    """Must find out that we're using wrong database name."""
    # arrange
    url = 'postgresql://user:password@127.0.0.1:5432/postgres'

    # act
    with patch.dict(os.environ, {constants.DB_ENV_VARIABLE: url}, clear=True):
        with pytest.raises(RuntimeError, match='using test database?'):
            safely_get_test_database()


@pytest.fixture(scope='session')
def functional_tests_db_uri():
    """Return database url."""
    return safely_get_test_database()


@pytest_asyncio.fixture(scope='session')
async def functional_tests_database(functional_tests_db_uri):
    """Return database."""
    db = None
    try:
        db = Database(functional_tests_db_uri)
        await db.connect()
        yield db
    except Exception as exc:
        print(f'Failed to initiate test database: {exc}')
    finally:
        if db is not None:
            await db.disconnect()


@pytest.fixture(scope='session')
def event_loop():
    """Overriding event loop fixture."""
    return asyncio.get_event_loop()


@pytest.fixture(scope='session')
def functional_tests_permanent_user():
    """Return permanent user (always exists in the database)."""
    return auth.User(
        uuid=UUID('00000000-0000-0000-0000-000000000000'),
        login='test-user',
        password='$2b$04$XRT/zbfYO8jB.M68OYMi'
                 'DOJRPSrGkK5m1iNiAYutDIBpf/9iHMHXm',
        name='test',
        root_item=UUID('00000000-0000-0000-0000-000000000000'),
    )


@pytest.fixture(scope='session')
def functional_tests_anon_user():
    """Return anon user."""
    return auth.User(
        uuid=None,
        login='test-anon',
        password='',
        name='anon',
        root_item=None,
    )


@pytest.fixture(scope='session')
def functional_tests_permanent_item():
    """Return permanent item (always exists in the database)."""
    return common.Item(
        uuid=UUID('00000000-0000-0000-0000-000000000000'),
        parent_uuid=None,
        owner_uuid=UUID('00000000-0000-0000-0000-000000000000'),
        number=0,
        name='test-item',
        is_collection=False,
        content_ext=None,
        preview_ext=None,
        thumbnail_ext=None,
        tags=[],
        permissions=[],
    )


# noinspection PyShadowingNames
@pytest.fixture(scope='session')
def items_write_repository(functional_tests_database):
    # FIXME - need different repo
    return asyncpg.ItemsWriteRepository(functional_tests_database)


@pytest.fixture(scope='session')
def functional_tests_policy(items_write_repository):
    return infra.Policy(items_repo=items_write_repository)


# noinspection PyShadowingNames
@pytest.fixture(scope='session')
def functional_tests_testing_repo(functional_tests_database):
    """Return repository for functional tests."""
    return RepositoryForTests(functional_tests_database)
