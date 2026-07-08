"""Global fixtures.

The DB-backed fixtures (async_database, make_user_model, ...) live in
``integration/conftest.py`` for historical reasons — they were written
when only integration tests existed. Smoke tests want the same
fixtures, so we register the integration conftest here as a pytest
plugin. Only the fixtures a test actually requests are ever exercised;
this doesn't change what runs for existing integration tests.

pytest requires ``pytest_plugins`` to sit in the root ``conftest.py``
(non-root usage has been deprecated since pytest 7).
"""

pytest_plugins = ['omoide.tests.integration.conftest']
