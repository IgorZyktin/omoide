"""Integration tests for omoide.omoide_api.items.item_use_cases.

Per CLAUDE.md §1 these MUST run against a real PostgreSQL instance and MUST
NOT mock the database, repos, or object storage. The fixtures wire up the
same async stack the API uses in production.
"""

from collections.abc import AsyncIterator
import uuid

import pytest
import sqlalchemy as sa

from omoide import exceptions
from omoide import models
from omoide.database import db_models
from omoide.object_storage.implementations.pgl_object_storage import PgLargeObjectStorage
from omoide.omoide_api.items.item_use_cases import DeleteItemUseCase
from omoide.omoide_api.items.item_use_cases import UploadItemUseCase


@pytest.fixture
def delete_item_use_case(
    async_database,
    items_repo,
    users_repo,
    meta_repo,
    tags_repo,
    commands_repo,
):
    """Build ``DeleteItemUseCase`` wired with real repos.

    Collapses the six constructor arguments into a single fixture so the
    tests below stay within the project's PLR0913 limit and remain easy
    to read.
    """
    return DeleteItemUseCase(
        async_database, items_repo, users_repo, meta_repo, tags_repo, commands_repo
    )


@pytest.fixture
def object_storage(async_database):
    """Real ``PgLargeObjectStorage`` backed by the test DB."""
    return PgLargeObjectStorage(async_database)


@pytest.fixture
def upload_item_use_case(
    async_database,
    items_repo,
    meta_repo,
    misc_repo,
    commands_repo,
    object_storage,
):
    """Build ``UploadItemUseCase`` wired with real repos + storage."""
    return UploadItemUseCase(
        async_database, items_repo, meta_repo, misc_repo, commands_repo, object_storage
    )


def _read_known_tags_user_counter(engine, user_id: int, tag: str) -> int | None:
    with engine.connect() as conn:
        row = conn.execute(
            sa.select(db_models.KnownTags.counter).where(
                db_models.KnownTags.user_id == user_id,
                db_models.KnownTags.tag == tag,
            )
        ).fetchone()
    return None if row is None else int(row.counter)


def _read_known_tags_anon_counter(engine, tag: str) -> int | None:
    with engine.connect() as conn:
        row = conn.execute(
            sa.select(db_models.KnownTagsAnon.counter).where(db_models.KnownTagsAnon.tag == tag)
        ).fetchone()
    return None if row is None else int(row.counter)


def _read_item_status(engine, item_id: int) -> int:
    with engine.connect() as conn:
        row = conn.execute(
            sa.select(db_models.Item.status).where(db_models.Item.id == item_id)
        ).fetchone()
    assert row is not None
    return int(row.status)


def _read_metainfo_deleted_at(engine, item_id: int):
    with engine.connect() as conn:
        row = conn.execute(
            sa.select(db_models.Metainfo.deleted_at).where(db_models.Metainfo.item_id == item_id)
        ).fetchone()
    assert row is not None
    return row.deleted_at


def _read_computed_tags(engine, item_id: int) -> list[str] | None:
    with engine.connect() as conn:
        row = conn.execute(
            sa.select(db_models.ComputedTags.tags).where(db_models.ComputedTags.item_id == item_id)
        ).fetchone()
    return None if row is None else list(row.tags)


def _read_parallel_ops(engine, name: str) -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(
            sa.select(db_models.ParallelOperation.extras).where(
                db_models.ParallelOperation.name == name
            )
        ).fetchall()
    return [dict(row.extras) for row in rows]


class TestDeleteItemUseCaseGuards:
    """Pre-condition / permission checks fire before any side effect."""

    async def test_anonymous_user_is_rejected(self, delete_item_use_case):
        use_case = delete_item_use_case
        with pytest.raises(exceptions.AccessDeniedError):
            await use_case.execute(
                user=models.User.new_anon(),
                item_uuid=uuid.uuid4(),
                desired_switch='parent',
            )

    async def test_unknown_item_uuid_raises(self, delete_item_use_case, make_user_model):
        actor = await make_user_model()
        use_case = delete_item_use_case
        with pytest.raises(exceptions.DoesNotExistError):
            await use_case.execute(
                user=actor,
                item_uuid=uuid.uuid4(),
                desired_switch='parent',
            )

    async def test_non_owner_is_rejected(
        self,
        delete_item_use_case,
        engine,
        make_user_model,
        make_item_model,
        make_metainfo,
    ):
        owner = await make_user_model()
        attacker = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        child = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
        )
        make_metainfo(child.id)

        use_case = delete_item_use_case
        with pytest.raises(exceptions.AccessDeniedError):
            await use_case.execute(
                user=attacker,
                item_uuid=child.uuid,
                desired_switch='parent',
            )

        # No side effects: item still alive.
        assert _read_item_status(engine, child.id) != models.Status.DELETED.value

    async def test_root_item_cannot_be_deleted(
        self,
        delete_item_use_case,
        engine,
        make_user_model,
        make_item_model,
        make_metainfo,
    ):
        owner = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        make_metainfo(root.id)

        use_case = delete_item_use_case
        with pytest.raises(exceptions.NotAllowedError):
            await use_case.execute(
                user=owner,
                item_uuid=root.uuid,
                desired_switch='parent',
            )

        assert _read_item_status(engine, root.id) != models.Status.DELETED.value


class TestDeleteItemUseCaseHappyPath:
    """Verify state mutations on a normal delete."""

    async def test_marks_item_as_deleted(
        self,
        delete_item_use_case,
        engine,
        make_user_model,
        make_item_model,
        make_metainfo,
    ):
        owner = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        child = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
        )
        make_metainfo(child.id)

        await delete_item_use_case.execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert _read_item_status(engine, child.id) == models.Status.DELETED.value

    async def test_marks_metainfo_as_deleted(
        self,
        delete_item_use_case,
        engine,
        make_user_model,
        make_item_model,
        make_metainfo,
    ):
        owner = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        child = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
        )
        make_metainfo(child.id)

        await delete_item_use_case.execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert _read_metainfo_deleted_at(engine, child.id) is not None

    async def test_clears_computed_tags(
        self,
        delete_item_use_case,
        engine,
        make_user_model,
        make_item_model,
        make_metainfo,
        set_computed_tags,
    ):
        owner = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        child = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
        )
        make_metainfo(child.id)
        set_computed_tags(child.id, {'red', 'blue'})

        await delete_item_use_case.execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert _read_computed_tags(engine, child.id) == []

    async def test_decrements_owner_known_tags(
        self,
        delete_item_use_case,
        engine,
        make_user_model,
        make_item_model,
        make_metainfo,
        set_computed_tags,
        set_known_tags_user,
    ):
        owner = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        child = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
        )
        make_metainfo(child.id)
        set_computed_tags(child.id, {'red'})
        set_known_tags_user(owner.id, {'red': 5})

        await delete_item_use_case.execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert _read_known_tags_user_counter(engine, owner.id, 'red') == 4

    async def test_decrements_anon_known_tags_when_owner_is_public(
        self,
        delete_item_use_case,
        engine,
        make_user_model,
        make_item_model,
        make_metainfo,
        set_computed_tags,
        set_known_tags_anon,
    ):
        owner = await make_user_model(is_public=True)
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        child = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
        )
        make_metainfo(child.id)
        set_computed_tags(child.id, {'red'})
        set_known_tags_anon({'red': 7})

        await delete_item_use_case.execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert _read_known_tags_anon_counter(engine, 'red') == 6

    async def test_does_not_touch_anon_tags_when_owner_is_private(
        self,
        delete_item_use_case,
        engine,
        make_user_model,
        make_item_model,
        make_metainfo,
        set_computed_tags,
        set_known_tags_anon,
    ):
        owner = await make_user_model(is_public=False)
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        child = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
        )
        make_metainfo(child.id)
        set_computed_tags(child.id, {'red'})
        set_known_tags_anon({'red': 7})

        await delete_item_use_case.execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert _read_known_tags_anon_counter(engine, 'red') == 7

    async def test_decrements_known_tags_for_permission_user(
        self,
        delete_item_use_case,
        engine,
        make_user_model,
        make_item_model,
        make_metainfo,
        set_computed_tags,
        set_known_tags_user,
    ):
        owner = await make_user_model()
        permitted = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        child = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
            permissions=[permitted.id],
        )
        make_metainfo(child.id)
        set_computed_tags(child.id, {'red'})
        set_known_tags_user(permitted.id, {'red': 3})

        await delete_item_use_case.execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert _read_known_tags_user_counter(engine, permitted.id, 'red') == 2


class TestDeleteItemUseCaseSwitchTo:
    """Verify the returned navigation target."""

    async def test_parent_mode_returns_parent(
        self,
        delete_item_use_case,
        make_user_model,
        make_item_model,
        make_metainfo,
    ):
        owner = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        child = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
        )
        make_metainfo(child.id)

        switch_to = await delete_item_use_case.execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert switch_to is not None
        assert switch_to.id == root.id

    async def test_sibling_mode_returns_next_sibling(
        self,
        delete_item_use_case,
        make_user_model,
        make_item_model,
        make_metainfo,
    ):
        owner = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        sibling_a = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
            number=1,
        )
        sibling_b = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
            number=2,
        )
        sibling_c = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
            number=3,
        )
        make_metainfo(sibling_b.id)
        _ = sibling_a, sibling_c

        switch_to = await delete_item_use_case.execute(
            user=owner,
            item_uuid=sibling_b.uuid,
            desired_switch='sibling',
        )

        assert switch_to is not None
        assert switch_to.id == sibling_c.id

    async def test_sibling_mode_returns_previous_when_at_end(
        self,
        delete_item_use_case,
        make_user_model,
        make_item_model,
        make_metainfo,
    ):
        owner = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        sibling_a = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
            number=1,
        )
        sibling_b = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
            number=2,
        )
        make_metainfo(sibling_b.id)

        switch_to = await delete_item_use_case.execute(
            user=owner,
            item_uuid=sibling_b.uuid,
            desired_switch='sibling',
        )

        assert switch_to is not None
        assert switch_to.id == sibling_a.id

    async def test_sibling_mode_falls_back_to_parent_for_collection_item(
        self,
        delete_item_use_case,
        make_user_model,
        make_item_model,
        make_metainfo,
    ):
        """Collections are excluded from ``get_siblings(collections=False)``.

        With ``item not in siblings`` the use case rewrites the switch
        target to the parent — verify the actual return value matches.
        """
        owner = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        collection = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
            is_collection=True,
        )
        make_metainfo(collection.id)

        switch_to = await delete_item_use_case.execute(
            user=owner,
            item_uuid=collection.uuid,
            desired_switch='sibling',
        )

        assert switch_to is not None
        assert switch_to.id == root.id

    async def test_sibling_mode_falls_back_to_parent_when_item_is_only_non_collection_sibling(
        self,
        delete_item_use_case,
        make_user_model,
        make_item_model,
        make_metainfo,
    ):
        """Regression: ``siblings[0]`` is the item being deleted.

        When the only non-collection sibling is the item itself, the
        correct behavior is to fall back to the parent rather than
        returning the (about-to-be-soft-deleted) item.
        """
        owner = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        lonely = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
            is_collection=False,
        )
        make_metainfo(lonely.id)

        switch_to = await delete_item_use_case.execute(
            user=owner,
            item_uuid=lonely.uuid,
            desired_switch='sibling',
        )

        assert switch_to is not None
        assert switch_to.id != lonely.id, 'switch_to must not be the item that was just deleted'
        assert switch_to.id == root.id


class TestDeleteItemUseCaseCascade:
    """Family-wide effects: descendants get the same treatment as the root of the delete."""

    async def test_soft_deletes_all_descendants(
        self,
        delete_item_use_case,
        engine,
        make_user_model,
        make_item_model,
        make_metainfo,
    ):
        owner = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        parent = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
            is_collection=True,
        )
        grand_child_a = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=parent.id,
            parent_uuid=parent.uuid,
        )
        grand_child_b = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=parent.id,
            parent_uuid=parent.uuid,
        )
        for item_id in (parent.id, grand_child_a.id, grand_child_b.id):
            make_metainfo(item_id)

        await delete_item_use_case.execute(
            user=owner,
            item_uuid=parent.uuid,
            desired_switch='parent',
        )

        for item_id in (parent.id, grand_child_a.id, grand_child_b.id):
            assert _read_item_status(engine, item_id) == models.Status.DELETED.value
            assert _read_metainfo_deleted_at(engine, item_id) is not None

    async def test_decrements_known_tags_for_descendants_own_permission_users(
        self,
        delete_item_use_case,
        engine,
        make_user_model,
        make_item_model,
        make_metainfo,
        set_computed_tags,
        set_known_tags_user,
    ):
        """Regression: ``item.permissions`` is used instead of ``member.permissions``.

        A descendant with its own permission user must have that user's
        ``known_tags`` counter decremented by the descendant's tags.
        Iterating the *root* item's permissions for every member would
        miss a descendant-only permission holder.
        """
        owner = await make_user_model()
        descendant_viewer = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        parent = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
            is_collection=True,
            permissions=[],
        )
        child = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=parent.id,
            parent_uuid=parent.uuid,
            permissions=[descendant_viewer.id],
        )
        for item_id in (parent.id, child.id):
            make_metainfo(item_id)

        set_computed_tags(parent.id, {'parent_only'})
        set_computed_tags(child.id, {'child_only'})
        set_known_tags_user(
            descendant_viewer.id,
            {'parent_only': 9, 'child_only': 9},
        )

        await delete_item_use_case.execute(
            user=owner,
            item_uuid=parent.uuid,
            desired_switch='parent',
        )

        # The viewer only saw the child, so only 'child_only' should drop.
        assert _read_known_tags_user_counter(engine, descendant_viewer.id, 'child_only') == 8, (
            'descendant-only permission holder must lose count for descendant tag'
        )
        assert _read_known_tags_user_counter(engine, descendant_viewer.id, 'parent_only') == 9, (
            'permission holder unrelated to parent must not lose count for parent tag'
        )


# --- UploadItemUseCase.mark_parent_as_collection ------------------------
#
# The upload flow walks every ancestor of the uploaded leaf and marks
# it as a collection with a shared thumbnail. The traversal used to
# early-return the moment it saw an ancestor that was already a
# collection with a thumbnail, silently skipping every higher ancestor
# that still needed the update. These tests pin the fixed behaviour:
# the walk ALWAYS reaches the root, and it emits an upload command
# only for ancestors that were actually missing the thumbnail.


async def _chunks_of(payload: bytes) -> AsyncIterator[bytes]:
    """Async iterator with a single chunk — a minimal fake upload body."""
    yield payload


async def _make_chain(make_item_model, owner, states):
    """Build a linear chain of items rooted at ``owner``.

    ``states`` is an iterable of ``(is_collection, thumbnail_ext)``
    tuples ordered from ROOT to LEAF. Returns the items in the same
    order so tests can index by depth.
    """
    items = []
    parent_id: int | None = None
    parent_uuid = None
    for is_collection, thumbnail_ext in states:
        item = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=parent_id,
            parent_uuid=parent_uuid,
            is_collection=is_collection,
            thumbnail_ext=thumbnail_ext,
        )
        items.append(item)
        parent_id = item.id
        parent_uuid = item.uuid
    return items


def _read_item_flags(engine, item_id: int):
    """Return ``(is_collection, thumbnail_ext)`` for one item."""
    with engine.connect() as conn:
        row = conn.execute(
            sa.select(
                db_models.Item.is_collection,
                db_models.Item.thumbnail_ext,
            ).where(db_models.Item.id == item_id)
        ).one()
    return row.is_collection, row.thumbnail_ext


def _read_upload_commands(engine) -> list[dict]:
    """Return every parallel command's ``extras`` dict."""
    with engine.connect() as conn:
        rows = conn.execute(sa.select(db_models.ParallelCommand.extras)).all()
    return [row.extras for row in rows]


def _read_notes(engine, item_id: int) -> dict[str, str]:
    """Return notes for the given item as a ``{key: value}`` dict."""
    with engine.connect() as conn:
        rows = conn.execute(
            sa.select(
                db_models.ItemNote.key,
                db_models.ItemNote.value,
            ).where(db_models.ItemNote.item_id == item_id)
        ).all()
    return {row.key: row.value for row in rows}


def _upload_file() -> models.NewFile:
    return models.NewFile(
        content_type='image/jpeg',
        filename='cat.jpg',
        ext='jpg',
        features=models.Features(extract_exif=False),
    )


class TestUploadItemUseCaseChain:
    """Every ancestor of the uploaded item gets flagged as a collection."""

    async def test_fresh_chain_flags_every_ancestor(
        self,
        upload_item_use_case,
        make_user_model,
        make_item_model,
        engine,
    ):
        """Baseline: nobody has been touched yet.

        Every ancestor MUST be marked as a collection with the placeholder
        ``thumbnail_ext='tmp'``, and a dedicated upload command MUST be
        enqueued for each ancestor, all sharing the leaf's OID.
        """
        alice = await make_user_model()
        root, mid, leaf = await _make_chain(
            make_item_model,
            alice,
            states=[
                (False, None),  # root
                (False, None),  # mid
                (False, None),  # leaf — upload target
            ],
        )

        await upload_item_use_case.execute(
            user=alice,
            item_uuid=leaf.uuid,
            file=_upload_file(),
            chunks=_chunks_of(b'x' * 128),
        )

        assert _read_item_flags(engine, root.id) == (True, 'tmp')
        assert _read_item_flags(engine, mid.id) == (True, 'tmp')
        # Leaf is not made a collection — it's the payload holder.
        # It gets ``status=PROCESSING`` and keeps ``thumbnail_ext=None``
        # until the converter fills it in.
        assert _read_item_flags(engine, leaf.id) == (False, None)

        # 3 commands, one per item (leaf + mid + root).
        commands = _read_upload_commands(engine)
        assert len(commands) == 3

        # Every command references the same OID (thumbnail sharing).
        oids = {cmd['oid'] for cmd in commands}
        assert len(oids) == 1

        # Ancestor commands are ``skip_content`` — they only need the
        # thumbnail rendered, not the original bytes.
        by_item = {cmd['item_id']: cmd for cmd in commands}
        assert by_item[leaf.id].get('skip_content') is not True
        assert by_item[mid.id]['skip_content'] is True
        assert by_item[root.id]['skip_content'] is True

        # A note is written on every ancestor linking back to the leaf.
        assert _read_notes(engine, mid.id)['copied_image_from'] == str(leaf.uuid)
        assert _read_notes(engine, root.id)['copied_image_from'] == str(leaf.uuid)

    async def test_walks_past_intermediate_already_done_ancestor(
        self,
        upload_item_use_case,
        make_user_model,
        make_item_model,
        engine,
    ):
        """Test intermediate update.

        The actual bug: an intermediate ancestor that already looks
        correct (``is_collection=True`` AND ``thumbnail_ext`` set) used
        to trigger an early ``return`` inside ``mark_parent_as_collection``,
        leaving every ancestor above it silently untouched. After the
        fix the walk continues to the root and updates it.
        """
        alice = await make_user_model()
        root, mid, leaf = await _make_chain(
            make_item_model,
            alice,
            states=[
                (False, None),  # root — MUST still be updated
                (True, 'jpg'),  # mid — already "done", not a wall
                (False, None),  # leaf — upload target
            ],
        )

        await upload_item_use_case.execute(
            user=alice,
            item_uuid=leaf.uuid,
            file=_upload_file(),
            chunks=_chunks_of(b'x' * 128),
        )

        # Root got its update — this is exactly what the bug prevented.
        assert _read_item_flags(engine, root.id) == (True, 'tmp')

        # Mid stays untouched: it already looks correct, no
        # skip_content command needed for it, no note written.
        assert _read_item_flags(engine, mid.id) == (True, 'jpg')

        commands = _read_upload_commands(engine)
        command_item_ids = {cmd['item_id'] for cmd in commands}
        # Two commands: leaf (payload) + root (thumbnail share). Mid
        # skipped because it already had a thumbnail.
        assert command_item_ids == {leaf.id, root.id}

        # Same OID shared across leaf and root.
        oids = {cmd['oid'] for cmd in commands}
        assert len(oids) == 1

        # Only root got the note — mid wasn't touched at all.
        assert _read_notes(engine, root.id)['copied_image_from'] == str(leaf.uuid)
        assert 'copied_image_from' not in _read_notes(engine, mid.id)
