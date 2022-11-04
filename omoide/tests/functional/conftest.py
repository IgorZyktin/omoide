# -*- coding: utf-8 -*-
"""Tests.
"""
import asyncio
import os
from uuid import UUID

import pytest
import pytest_asyncio
import sqlalchemy
from databases import Database

from omoide import domain
from omoide import infra
from omoide.presentation import api_models
from omoide.storage import repositories
from omoide.storage.database import models


@pytest_asyncio.fixture(scope='session')
async def database():
    url = os.environ.get('OMOIDE_TEST_DB_URL')

    if url is None:
        raise RuntimeError('You must specify test database url to start')

    db = None
    try:
        engine = sqlalchemy.create_engine(url)
        models.metadata.create_all(bind=engine)
        engine.dispose()

        db = Database(url)
        await db.connect()
        yield db
    except Exception as e:
        print(f'Failed to initiate test database: {e}')
    finally:
        if db is not None:
            await db.disconnect()


@pytest.fixture(scope='session')
def items_repository(database):
    return repositories.ItemsRepository(database)


@pytest.fixture(scope='session')
def metainfo_repository(database):
    return repositories.MetainfoRepository(database)


@pytest.fixture(scope='session')
def policy(items_repository):
    return infra.Policy(items_repo=items_repository)


@pytest.fixture(scope='session')
def event_loop():
    """Overriding event loop fixture."""
    return asyncio.get_event_loop()


@pytest_asyncio.fixture(scope='session')
async def user(database):
    await database.execute(
        """
        DELETE FROM users WHERE uuid = '00000000-0000-0000-0000-000000000000'
        """
    )
    await database.execute(
        """
        INSERT INTO
        users (uuid, login, password, name, root_item)
        VALUES (
        '00000000-0000-0000-0000-000000000000',
        'test',
        'test',
         'test',
         null
         );
        """,
    )
    await database.execute(
        """
        INSERT INTO
        items (
        uuid,
        parent_uuid,
        owner_uuid,
        number,
        name,
        is_collection,
        content_ext,
        preview_ext,
        thumbnail_ext,
        tags,
        permissions
        )
        VALUES (
        '00000000-0000-0000-0000-000000000000',
        null,
        '00000000-0000-0000-0000-000000000000',
        1,
        'test item',
        false,
        null,
        null,
        null,
        ARRAY []::text[],
        ARRAY []::text[]
         );
        """,
    )
    yield domain.User(
        uuid=UUID('00000000-0000-0000-0000-000000000000'),
        login='test',
        password='test',
        name='test',
        root_item=UUID('00000000-0000-0000-0000-000000000000'),
    )
    await database.execute(
        """
        DELETE FROM users WHERE uuid = '00000000-0000-0000-0000-000000000000'
        """
    )


@pytest_asyncio.fixture(scope='session')
def anon_user():
    return domain.User.new_anon()


@pytest.fixture
def raw_item_in():
    """Raw item from user."""
    return api_models.CreateItemIn(
        name='Test item',
        is_collection=False,
        tags=['tag-1', 'tag-2', 'tag-3'],
        permissions=[],
    )
