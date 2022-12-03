# -*- coding: utf-8 -*-
"""Tests.
"""
import os

import pytest

from omoide.daemons.worker.db import Database


@pytest.fixture(scope='package')
def worker_database():
    db_url = os.environ['OMOIDE_DB_URL_TEST_SYNC']

    if not db_url:
        raise RuntimeError('No test database specified')

    database = Database(db_url)

    with database.life_cycle(echo=True):
        yield database
