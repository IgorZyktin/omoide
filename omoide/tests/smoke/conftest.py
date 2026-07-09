"""Bring integration DB fixtures into the smoke test scope.

The DB-backed fixtures (``async_database``, ``make_user_model``,
``make_item_model``, ``engine``, ...) live in ``integration/conftest.py``.
Re-importing them here makes them discoverable to smoke tests as well,
without going through ``pytest_plugins`` (which conflicts with the
plain-conftest auto-discovery pytest does inside ``integration/``).
"""

from omoide.tests.integration.conftest import _schema_engine  # noqa: F401
from omoide.tests.integration.conftest import async_database  # noqa: F401
from omoide.tests.integration.conftest import async_db_url  # noqa: F401
from omoide.tests.integration.conftest import commands_repo  # noqa: F401
from omoide.tests.integration.conftest import engine  # noqa: F401
from omoide.tests.integration.conftest import items_repo  # noqa: F401
from omoide.tests.integration.conftest import make_item  # noqa: F401
from omoide.tests.integration.conftest import make_item_model  # noqa: F401
from omoide.tests.integration.conftest import make_metainfo  # noqa: F401
from omoide.tests.integration.conftest import make_user  # noqa: F401
from omoide.tests.integration.conftest import make_user_model  # noqa: F401
from omoide.tests.integration.conftest import meta_repo  # noqa: F401
from omoide.tests.integration.conftest import metrics_collector  # noqa: F401
from omoide.tests.integration.conftest import misc_repo  # noqa: F401
from omoide.tests.integration.conftest import set_computed_tags  # noqa: F401
from omoide.tests.integration.conftest import set_known_tags_anon  # noqa: F401
from omoide.tests.integration.conftest import set_known_tags_user  # noqa: F401
from omoide.tests.integration.conftest import signatures_repo  # noqa: F401
from omoide.tests.integration.conftest import tags_repo  # noqa: F401
from omoide.tests.integration.conftest import test_db_url  # noqa: F401
from omoide.tests.integration.conftest import users_repo  # noqa: F401
