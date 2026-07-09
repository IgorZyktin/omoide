"""Bring integration DB fixtures into the smoke test scope.

The DB-backed fixtures (``async_database``, ``make_user_model``,
``make_item_model``, ``engine``, ...) live in ``integration/conftest.py``.
Re-importing them here makes them discoverable to smoke tests as well,
without going through ``pytest_plugins`` (which conflicts with the
plain-conftest auto-discovery pytest does inside ``integration/``).
"""

from omoide.tests.integration.conftest import (  # noqa: F401
    _schema_engine,
    async_database,
    async_db_url,
    commands_repo,
    engine,
    items_repo,
    make_item,
    make_item_model,
    make_metainfo,
    make_user,
    make_user_model,
    meta_repo,
    metrics_collector,
    misc_repo,
    set_computed_tags,
    set_known_tags_anon,
    set_known_tags_user,
    signatures_repo,
    tags_repo,
    test_db_url,
    users_repo,
)
