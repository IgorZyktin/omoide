"""Smoke tests for ``api_upload_item``.

Per CLAUDE.md §1 these run against a real PostgreSQL instance — only
the auth-related dependencies are overridden (so tests don't need to
bcrypt-hash passwords). Repos, object storage, use case, and the whole
request lifecycle run the same code path as production.

Coverage focus:
* Happy path — file within limits, valid extension.
* Size validation — the fix for the top-5 review's bug #2:
  * Content-Length exceeds ``limits.MAX_MEDIA_SIZE`` → 403.
  * Malformed ``Content-Length`` header → 400.
* Extension filter — unsupported extensions → 400.
* AuthZ — anonymous callers → 403 via ``get_known_user``;
  non-owner callers → 403 via the use case's ownership check.
* Missing item — unknown UUID → 404 from the use case.
"""

from uuid import uuid4

import pytest
from httpx import ASGITransport
from httpx import AsyncClient

from omoide import dependencies as dep
from omoide import limits
from omoide.object_storage.implementations.pgl_object_storage import PgLargeObjectStorage
from omoide.omoide_api.application import apply_api_routes_v1
from omoide.omoide_api.application import get_api


# --- fixtures ----------------------------------------------------------


@pytest.fixture
def api_app(async_database):
    """Fresh api-only FastAPI instance wired to the test DB.

    The api is normally mounted at ``/api`` inside the main app; here
    we use it standalone so paths in tests start with ``/v1/...``.
    """
    app = get_api()
    apply_api_routes_v1(app)

    storage = PgLargeObjectStorage(async_database)
    app.dependency_overrides[dep.get_database] = lambda: async_database
    app.dependency_overrides[dep.get_object_storage] = lambda: storage

    yield app
    app.dependency_overrides.clear()


def _authenticate_as(app, user):
    """Wire the DI so every request runs as ``user`` (skipping bcrypt)."""
    app.dependency_overrides[dep.get_current_user] = lambda: user
    app.dependency_overrides[dep.get_known_user] = lambda: user


@pytest.fixture
async def http_client(api_app):
    """Async HTTP client bound to the api app via ASGI transport.

    Async client is needed because the underlying FastAPI dependencies
    are async — using the sync ``TestClient`` from inside an async test
    creates a nested event loop.
    """
    transport = ASGITransport(app=api_app)
    async with AsyncClient(
        transport=transport, base_url='http://testserver'
    ) as client:
        yield client


# --- happy path --------------------------------------------------------


class TestHappyPath:
    async def test_uploads_small_file(
        self,
        api_app,
        http_client,
        make_user_model,
        make_item_model,
    ):
        user = await make_user_model()
        item = await make_item_model(owner_id=user.id, owner_uuid=user.uuid)
        _authenticate_as(api_app, user)

        response = await http_client.put(
            f'/v1/items/{item.uuid}/upload',
            files={'file': ('cat.jpg', b'\xff\xd8\xff' + b'x' * 100, 'image/jpeg')},
        )

        assert response.status_code == 202
        body = response.json()
        assert body['result'] == 'enqueued content adding'
        assert body['item_uuid'] == str(item.uuid)


# --- size validation ---------------------------------------------------


class TestSizeValidation:
    async def test_rejects_when_content_length_exceeds_limit(
        self,
        api_app,
        http_client,
        make_user_model,
        make_item_model,
        monkeypatch,
    ):
        """Content-Length header check — the early-out on oversized
        uploads that stops the client from streaming any bytes at all."""
        monkeypatch.setattr(limits, 'MAX_MEDIA_SIZE', 100)
        monkeypatch.setattr(limits, 'MAX_MEDIA_SIZE_HR', '100 B')

        user = await make_user_model()
        item = await make_item_model(owner_id=user.id, owner_uuid=user.uuid)
        _authenticate_as(api_app, user)

        response = await http_client.put(
            f'/v1/items/{item.uuid}/upload',
            files={'file': ('big.jpg', b'x' * 2000, 'image/jpeg')},
        )

        assert response.status_code == 403
        assert 'Maximum upload size' in response.json()['message']
        assert '100 B' in response.json()['message']

    async def test_rejects_when_content_length_is_not_a_number(
        self,
        api_app,
        http_client,
        make_user_model,
        make_item_model,
    ):
        """Malformed ``Content-Length`` header → 400.

        Previously the controller did ``int(headers['content-length'])``
        with no error handling; a bogus value crashed the request as a
        500 ``ValueError`` instead of a 4xx client error.
        """
        user = await make_user_model()
        item = await make_item_model(owner_id=user.id, owner_uuid=user.uuid)
        _authenticate_as(api_app, user)

        response = await http_client.put(
            f'/v1/items/{item.uuid}/upload',
            files={'file': ('cat.jpg', b'x' * 100, 'image/jpeg')},
            headers={'Content-Length': 'not-a-number'},
        )

        assert response.status_code == 400
        assert 'Content-Length' in response.json()['message']

    async def test_within_limit_uploads_ok(
        self,
        api_app,
        http_client,
        make_user_model,
        make_item_model,
        monkeypatch,
    ):
        """Sanity: with the limit at exactly the payload size, upload
        succeeds. Guards against off-by-one in the ``>`` comparison."""
        # Multipart adds boundary + headers; give plenty of headroom.
        monkeypatch.setattr(limits, 'MAX_MEDIA_SIZE', 10_000)
        monkeypatch.setattr(limits, 'MAX_MEDIA_SIZE_HR', '10 KB')

        user = await make_user_model()
        item = await make_item_model(owner_id=user.id, owner_uuid=user.uuid)
        _authenticate_as(api_app, user)

        response = await http_client.put(
            f'/v1/items/{item.uuid}/upload',
            files={'file': ('cat.jpg', b'x' * 500, 'image/jpeg')},
        )

        assert response.status_code == 202


# --- extension filter --------------------------------------------------


class TestExtensionFilter:
    async def test_rejects_unsupported_extension(
        self,
        api_app,
        http_client,
        make_user_model,
        make_item_model,
    ):
        user = await make_user_model()
        item = await make_item_model(owner_id=user.id, owner_uuid=user.uuid)
        _authenticate_as(api_app, user)

        response = await http_client.put(
            f'/v1/items/{item.uuid}/upload',
            files={
                'file': (
                    'malicious.exe',
                    b'MZ' + b'\x00' * 100,
                    'application/octet-stream',
                )
            },
        )

        assert response.status_code == 400
        assert 'extension' in response.json()['message'].lower()

    async def test_accepts_uppercase_extension(
        self,
        api_app,
        http_client,
        make_user_model,
        make_item_model,
    ):
        """The controller lower-cases before matching; capitalised
        extensions must still be accepted."""
        user = await make_user_model()
        item = await make_item_model(owner_id=user.id, owner_uuid=user.uuid)
        _authenticate_as(api_app, user)

        response = await http_client.put(
            f'/v1/items/{item.uuid}/upload',
            files={'file': ('CAT.JPG', b'\xff\xd8\xff' + b'x' * 100, 'image/jpeg')},
        )

        assert response.status_code == 202


# --- authorization -----------------------------------------------------


class TestAuthorization:
    async def test_anonymous_caller_is_rejected(
        self,
        http_client,
        make_user_model,
        make_item_model,
    ):
        """No auth overrides on the app → get_current_user returns anon
        → get_known_user raises 403."""
        user = await make_user_model()
        item = await make_item_model(owner_id=user.id, owner_uuid=user.uuid)
        # Deliberately NOT calling _authenticate_as.

        response = await http_client.put(
            f'/v1/items/{item.uuid}/upload',
            files={'file': ('cat.jpg', b'x' * 100, 'image/jpeg')},
        )

        assert response.status_code == 403

    async def test_non_owner_is_rejected(
        self,
        api_app,
        http_client,
        make_user_model,
        make_item_model,
    ):
        """Item belongs to someone else — use case's ownership check
        raises ``NotAllowedError`` → 403."""
        owner = await make_user_model()
        item = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)

        intruder = await make_user_model()
        _authenticate_as(api_app, intruder)

        response = await http_client.put(
            f'/v1/items/{item.uuid}/upload',
            files={'file': ('cat.jpg', b'x' * 100, 'image/jpeg')},
        )

        assert response.status_code == 403


# --- missing item ------------------------------------------------------


class TestMissingItem:
    async def test_returns_404_for_unknown_uuid(
        self,
        api_app,
        http_client,
        make_user_model,
    ):
        user = await make_user_model()
        _authenticate_as(api_app, user)

        response = await http_client.put(
            f'/v1/items/{uuid4()}/upload',
            files={'file': ('cat.jpg', b'x' * 100, 'image/jpeg')},
        )

        assert response.status_code == 404
