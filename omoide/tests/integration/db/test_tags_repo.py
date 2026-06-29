"""Tests for ``TagsRepo`` counter operations on ``known_tags`` / ``known_tags_anon``.

Background: the previous implementation looped tag-by-tag with bare
``UPDATE`` — N round-trips, and tags that did not yet have a row in
``known_tags`` silently no-opped, so a brand-new tag never reached
autocomplete until ``rebuild_known_tags`` ran. The fix:

* ``increment_*`` — single ``INSERT ... ON CONFLICT DO UPDATE`` so
  unknown tags get a row with ``counter = 1`` and known ones go up by 1
  (floored at 0 first to absorb any prior negative drift).
* ``decrement_*`` — single bulk ``UPDATE ... WHERE tag = ANY(...)``,
  floored at 0. Decrement does NOT create rows.

Tests below pin both behaviours.
"""

from uuid import uuid4

import sqlalchemy as sa

from omoide.database import db_models


# --- read helpers ------------------------------------------------------


def _user_counter(engine, user_id: int, tag: str) -> int | None:
    """Return the counter for one (user_id, tag) row, or None if absent."""
    with engine.connect() as conn:
        row = conn.execute(
            sa.select(db_models.KnownTags.counter).where(
                db_models.KnownTags.user_id == user_id,
                db_models.KnownTags.tag == tag,
            )
        ).fetchone()
    return None if row is None else int(row.counter)


def _anon_counter(engine, tag: str) -> int | None:
    """Return the anon counter for one tag, or None if absent."""
    with engine.connect() as conn:
        row = conn.execute(
            sa.select(db_models.KnownTagsAnon.counter).where(
                db_models.KnownTagsAnon.tag == tag
            )
        ).fetchone()
    return None if row is None else int(row.counter)


def _user_rows(engine, user_id: int) -> dict[str, int]:
    """Snapshot all (tag, counter) for a user."""
    with engine.connect() as conn:
        rows = conn.execute(
            sa.select(
                db_models.KnownTags.tag, db_models.KnownTags.counter
            ).where(db_models.KnownTags.user_id == user_id)
        ).fetchall()
    return {row.tag: int(row.counter) for row in rows}


# --- increment_known_tags_user ----------------------------------------


class TestIncrementKnownTagsUser:
    async def test_empty_tags_is_noop(
        self,
        async_database,
        tags_repo,
        make_user_model,
        engine,
    ):
        user = await make_user_model()

        async with async_database.transaction() as conn:
            await tags_repo.increment_known_tags_user(conn, user, set())

        assert _user_rows(engine, user.id) == {}

    async def test_creates_row_for_previously_unknown_tag(
        self,
        async_database,
        tags_repo,
        make_user_model,
        engine,
    ):
        """The original bug: ``UPDATE`` against a missing row no-ops.

        After the fix the first sighting of a tag MUST create the row
        with counter=1 — otherwise autocomplete never learns about it.
        """
        user = await make_user_model()

        async with async_database.transaction() as conn:
            await tags_repo.increment_known_tags_user(conn, user, {'new_tag'})

        assert _user_counter(engine, user.id, 'new_tag') == 1

    async def test_increments_existing_row(
        self,
        async_database,
        tags_repo,
        make_user_model,
        set_known_tags_user,
        engine,
    ):
        user = await make_user_model()
        set_known_tags_user(user.id, {'cats': 5})

        async with async_database.transaction() as conn:
            await tags_repo.increment_known_tags_user(conn, user, {'cats'})

        assert _user_counter(engine, user.id, 'cats') == 6

    async def test_clamps_negative_counter_to_zero_then_adds_one(
        self,
        async_database,
        tags_repo,
        make_user_model,
        set_known_tags_user,
        engine,
    ):
        """If the counter has drifted negative (legacy bug), the
        ``greatest(0, counter) + 1`` guard MUST treat it as zero so the
        next increment lands at 1 — not at, say, -4."""
        user = await make_user_model()
        set_known_tags_user(user.id, {'drifted': -5})

        async with async_database.transaction() as conn:
            await tags_repo.increment_known_tags_user(conn, user, {'drifted'})

        assert _user_counter(engine, user.id, 'drifted') == 1

    async def test_handles_mix_of_known_and_unknown_tags(
        self,
        async_database,
        tags_repo,
        make_user_model,
        set_known_tags_user,
        engine,
    ):
        """One call must service both kinds correctly in a single
        round-trip — verified by the absence of explicit ordering."""
        user = await make_user_model()
        set_known_tags_user(user.id, {'old': 3})

        async with async_database.transaction() as conn:
            await tags_repo.increment_known_tags_user(
                conn, user, {'old', 'fresh-1', 'fresh-2'}
            )

        assert _user_rows(engine, user.id) == {
            'old': 4,
            'fresh-1': 1,
            'fresh-2': 1,
        }

    async def test_isolated_per_user(
        self,
        async_database,
        tags_repo,
        make_user_model,
        set_known_tags_user,
        engine,
    ):
        """Tags share the same name across users; counters MUST NOT mix."""
        alice = await make_user_model()
        bob = await make_user_model()
        set_known_tags_user(alice.id, {'shared': 10})
        set_known_tags_user(bob.id, {'shared': 10})

        async with async_database.transaction() as conn:
            await tags_repo.increment_known_tags_user(conn, alice, {'shared'})

        assert _user_counter(engine, alice.id, 'shared') == 11
        assert _user_counter(engine, bob.id, 'shared') == 10


# --- increment_known_tags_anon ----------------------------------------


class TestIncrementKnownTagsAnon:
    async def test_empty_tags_is_noop(self, async_database, tags_repo, engine):
        async with async_database.transaction() as conn:
            await tags_repo.increment_known_tags_anon(conn, set())

        with engine.connect() as conn:
            count = conn.execute(
                sa.select(sa.func.count()).select_from(db_models.KnownTagsAnon)
            ).scalar_one()
        assert count == 0

    async def test_creates_row_for_unknown_tag(
        self, async_database, tags_repo, engine
    ):
        async with async_database.transaction() as conn:
            await tags_repo.increment_known_tags_anon(conn, {'fresh'})

        assert _anon_counter(engine, 'fresh') == 1

    async def test_increments_and_creates_in_one_call(
        self,
        async_database,
        tags_repo,
        set_known_tags_anon,
        engine,
    ):
        set_known_tags_anon({'known': 4})

        async with async_database.transaction() as conn:
            await tags_repo.increment_known_tags_anon(
                conn, {'known', 'unknown'}
            )

        assert _anon_counter(engine, 'known') == 5
        assert _anon_counter(engine, 'unknown') == 1

    async def test_clamps_negative_to_zero(
        self,
        async_database,
        tags_repo,
        set_known_tags_anon,
        engine,
    ):
        set_known_tags_anon({'negative': -3})

        async with async_database.transaction() as conn:
            await tags_repo.increment_known_tags_anon(conn, {'negative'})

        assert _anon_counter(engine, 'negative') == 1


# --- decrement_known_tags_user ----------------------------------------


class TestDecrementKnownTagsUser:
    async def test_empty_tags_is_noop(
        self,
        async_database,
        tags_repo,
        make_user_model,
        set_known_tags_user,
        engine,
    ):
        user = await make_user_model()
        set_known_tags_user(user.id, {'kept': 5})

        async with async_database.transaction() as conn:
            await tags_repo.decrement_known_tags_user(conn, user, set())

        assert _user_counter(engine, user.id, 'kept') == 5

    async def test_decrements_existing_row(
        self,
        async_database,
        tags_repo,
        make_user_model,
        set_known_tags_user,
        engine,
    ):
        user = await make_user_model()
        set_known_tags_user(user.id, {'cats': 5})

        async with async_database.transaction() as conn:
            await tags_repo.decrement_known_tags_user(conn, user, {'cats'})

        assert _user_counter(engine, user.id, 'cats') == 4

    async def test_does_not_create_row_for_unknown_tag(
        self,
        async_database,
        tags_repo,
        make_user_model,
        engine,
    ):
        """Decrementing what was never incremented is a no-op — we do
        NOT want zero-rows polluting autocomplete (which filters by
        ``counter > 0`` anyway)."""
        user = await make_user_model()

        async with async_database.transaction() as conn:
            await tags_repo.decrement_known_tags_user(
                conn, user, {'never_seen'}
            )

        assert _user_counter(engine, user.id, 'never_seen') is None

    async def test_floors_at_zero(
        self,
        async_database,
        tags_repo,
        make_user_model,
        set_known_tags_user,
        engine,
    ):
        user = await make_user_model()
        set_known_tags_user(user.id, {'depleting': 1})

        async with async_database.transaction() as conn:
            await tags_repo.decrement_known_tags_user(conn, user, {'depleting'})
            await tags_repo.decrement_known_tags_user(conn, user, {'depleting'})
            await tags_repo.decrement_known_tags_user(conn, user, {'depleting'})

        assert _user_counter(engine, user.id, 'depleting') == 0

    async def test_bulk_decrement_matches_only_provided_tags(
        self,
        async_database,
        tags_repo,
        make_user_model,
        set_known_tags_user,
        engine,
    ):
        user = await make_user_model()
        set_known_tags_user(user.id, {'a': 10, 'b': 10, 'c': 10})

        async with async_database.transaction() as conn:
            await tags_repo.decrement_known_tags_user(conn, user, {'a', 'c'})

        assert _user_rows(engine, user.id) == {'a': 9, 'b': 10, 'c': 9}

    async def test_does_not_touch_other_users(
        self,
        async_database,
        tags_repo,
        make_user_model,
        set_known_tags_user,
        engine,
    ):
        alice = await make_user_model()
        bob = await make_user_model()
        set_known_tags_user(alice.id, {'shared': 10})
        set_known_tags_user(bob.id, {'shared': 10})

        async with async_database.transaction() as conn:
            await tags_repo.decrement_known_tags_user(conn, alice, {'shared'})

        assert _user_counter(engine, alice.id, 'shared') == 9
        assert _user_counter(engine, bob.id, 'shared') == 10


# --- decrement_known_tags_anon ----------------------------------------


class TestDecrementKnownTagsAnon:
    async def test_empty_tags_is_noop(
        self,
        async_database,
        tags_repo,
        set_known_tags_anon,
        engine,
    ):
        set_known_tags_anon({'kept': 5})

        async with async_database.transaction() as conn:
            await tags_repo.decrement_known_tags_anon(conn, set())

        assert _anon_counter(engine, 'kept') == 5

    async def test_decrements_existing_row(
        self,
        async_database,
        tags_repo,
        set_known_tags_anon,
        engine,
    ):
        set_known_tags_anon({'cats': 5})

        async with async_database.transaction() as conn:
            await tags_repo.decrement_known_tags_anon(conn, {'cats'})

        assert _anon_counter(engine, 'cats') == 4

    async def test_does_not_create_row_for_unknown_tag(
        self, async_database, tags_repo, engine
    ):
        unknown_tag = f'never-{uuid4()}'

        async with async_database.transaction() as conn:
            await tags_repo.decrement_known_tags_anon(conn, {unknown_tag})

        assert _anon_counter(engine, unknown_tag) is None

    async def test_floors_at_zero(
        self,
        async_database,
        tags_repo,
        set_known_tags_anon,
        engine,
    ):
        set_known_tags_anon({'depleting': 1})

        async with async_database.transaction() as conn:
            await tags_repo.decrement_known_tags_anon(conn, {'depleting'})
            await tags_repo.decrement_known_tags_anon(conn, {'depleting'})
            await tags_repo.decrement_known_tags_anon(conn, {'depleting'})

        assert _anon_counter(engine, 'depleting') == 0
