# CLAUDE.md

Instructions for Claude Code and other coding agents working on this repo.
Auto-loaded by Claude Code. Other agents: read this before any code change.

## Project

Omoide — image/video storage with tag-based search.
Stack: Python 3.12, FastAPI, async SQLAlchemy 2 (asyncpg), PostgreSQL,
Pydantic v2, Jinja2, custom background workers (serial / parallel / converter /
downloader). Entry: `omoide/application.py`. Migrations: `alembic/`.

---

# Testing policy

This codebase has near-zero test coverage. Every change MUST add tests per
the rules below. This file is the single source of truth — if it conflicts
with habits from other projects, follow this file.

## 1. Test layers (in priority order)

| Layer | Default for | Real Postgres? | Real FS? |
|-------|-------------|----------------|----------|
| **Integration** | use-cases, repositories, workers, object storage, mediators | **YES** | YES (tmp_path) |
| **Smoke (HTTP)** | every controller endpoint | **YES** | YES (tmp_path) |
| **Unit** | pure functions, value-object methods, math, parsing | NO | NO |

The pyramid is intentionally **integration-heavy**. Mocking the DB defeats
the purpose: most bugs in this repo live in SQL, transaction boundaries,
JSONB queries, GIN-indexed array lookups, and worker lifecycles.

## 2. MUST / MUST NOT

### MUST

- Use a real PostgreSQL instance for every integration and smoke test.
- Read the test DB URL from the env var `OMOIDE_TEST_DB_URL`. Fail loudly
  if it is unset — never silently fall back to a localhost default.
- Isolate tests via per-test transaction rollback. The `connection`
  fixture (see §4) MUST wrap each test in a transaction that is rolled
  back on teardown.
- Cover, for each use-case: happy path + every exception class it can
  raise (`DoesNotExistError`, `NotAllowedError`, `InvalidInputError`, …).
- For workers: assert the resulting state of the queue/operation tables
  (`serial_operations`, `parallel_operations`, `queue_input_media`,
  `queue_output_media`) — not just that the function returned.
- For controllers: assert HTTP status **and** the persisted side effect
  (DB row, queue entry, file on disk). Status-only is not enough.
- Build domain users via `models.User.new_anon()` (for anon) or via the
  `make_user` factory (see §4). Never hand-construct.
- Patch time via `pu.now()` at the boundary if a test depends on it.

### MUST NOT

- DO NOT mock `AbsDatabase`, any `Abs*Repo`, or `AbsObjectStorage` in
  tests that exercise use-cases, controllers, or workers. Use the real
  SQLAlchemy implementation against the test DB.
- DO NOT skip writing a test because Postgres setup is "heavy" — the
  fixtures are designed to make it cheap (one engine per session, one
  transaction per test).
- DO NOT use `time.sleep`, `asyncio.sleep`, or wall-clock waits in tests.
- DO NOT assert only on stringification, types, or repr output. Assert
  observable behavior (returned values, DB state, HTTP responses).
- DO NOT hard-code DB URLs, table names, schema names, or absolute file
  paths into tests. Use fixtures and `tmp_path`.
- DO NOT mark tests `xfail` or `skip` to land green. Either fix the
  test or fix the code.

## 3. Directory layout (target)

```
omoide/tests/
├── conftest.py                # global fixtures
├── unit/                      # existing — pure functions only
│   └── …
├── integration/
│   ├── conftest.py            # DB-backed fixtures + entity factories
│   ├── api/                   # mirrors omoide/omoide_api/
│   │   └── items/test_item_use_cases.py
│   ├── app/                   # mirrors omoide/omoide_app/
│   ├── db/                    # mirrors omoide/database/implementations/
│   ├── object_storage/
│   └── workers/
│       ├── converter/
│       ├── downloader/
│       ├── serial/
│       └── parallel/
└── smoke/
    ├── api/                   # TestClient → /api/...
    └── app/                   # TestClient → /...
```

**Path mapping rule**: `omoide/<path>/<mod>.py` → `omoide/tests/<layer>/<path>/test_<mod>.py`.
One test module per production module. Group related tests in one class.

## 4. Required fixtures (in `omoide/tests/integration/conftest.py`)

The fixtures below are the public contract. New tests MUST consume them
and MUST NOT replicate their logic inline.

```python
# Session-scoped: provisioning
@pytest.fixture(scope='session')
def test_db_url() -> str: ...                          # reads OMOIDE_TEST_DB_URL
@pytest.fixture(scope='session')
async def engine(test_db_url) -> AsyncEngine: ...      # create_all once

# Function-scoped: isolation
@pytest.fixture
async def connection(engine) -> AsyncConnection: ...   # BEGIN … ROLLBACK

# Function-scoped: composition
@pytest.fixture
def mediator(connection) -> mediators.Mediator: ...    # real repos, shared conn

# Factories — persist and return domain models
@pytest.fixture
def make_user(connection): ...                         # role, public, lang…
@pytest.fixture
def make_item(connection, make_user): ...              # parent, tags, perms…
@pytest.fixture
def make_metainfo(connection): ...
@pytest.fixture
def make_input_media(connection): ...                  # for converter tests
```

Each factory MUST accept `**overrides` so a test can vary one field
without restating the rest.

## 5. Running

```bash
# Full suite
OMOIDE_TEST_DB_URL="postgresql+asyncpg://omoide:omoide@localhost:5433/omoide_test" \
  uv run pytest

# Narrow scope
uv run pytest omoide/tests/integration/api/items -x

# Pattern + fail-fast
uv run pytest -x -k "upload and large_object"

# Coverage
uv run pytest --cov=omoide --cov-branch --cov-report=term-missing
```

Pytest configuration lives in `pyproject.toml` (`[tool.pytest.ini_options]`).
`asyncio_mode = "auto"` is set, so `async def` tests need no decorator.

## 6. CI requirements

- CI MUST start an isolated PostgreSQL service before running tests.
- The test DB MUST have `pg_trgm` and `btree_gin` extensions enabled
  (see `db_models.KnownTags` docstring).
- Coverage gate for **new** code: ≥80 % line + branch.
- A PR that adds or modifies a use-case without a corresponding
  integration test MUST be rejected at review.

## 7. Priority backlog

Write these tests first — highest-risk uncovered areas:

1. `omoide_api/items/item_use_cases.py::UploadItemUseCase` — large-file
   path with shared OID + parent-thumbnail propagation. Recently
   refactored, zero coverage.
2. `omoide/workers/converter/__main__.py::do_work` together with
   `ConverterPostgreSQLDatabase.is_oid_referenced_elsewhere` — the OID
   reference-count logic. Test both branches (other-references-exist /
   no-references) and the failure path.
3. `CreateOneItemUseCase` / `CreateManyItemsUseCase` — root of the data
   model, touches tags, known-tags caches, permissions.
4. `DeleteItemUseCase` — multi-table side effects: family traversal,
   tag decrement, object-storage parallel operations, soft-delete.
5. `ChangePermissionsUseCase` — emits a `rebuild_permissions` serial
   operation; the operation extras must be exact.
6. `SearchRepo` / `BrowseRepo` — pagination, tag include/exclude with
   GIN indexes, anon vs known-user paths.
7. `UsersRepo.get_root_item` and the cascade of computed-tags updates.

## 8. When in doubt

- If a test for the change does not fit into any layer above, ASK the
  user before writing it in a fourth location.
- If a test would require mocking the DB to be feasible, the test is
  wrong — restructure the code under test or write the integration test.
- Adding a fixture? Put it in `omoide/tests/integration/conftest.py`
  and document its contract in the docstring.
