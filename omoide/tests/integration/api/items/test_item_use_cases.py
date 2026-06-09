"""Integration tests for omoide.omoide_api.items.item_use_cases.

Per CLAUDE.md §1 these MUST run against a real PostgreSQL instance and MUST
NOT mock the database, repos, or object storage. The fixtures wire up the
same async stack the API uses in production.

Three tests in this module document bugs identified during code review of
``DeleteItemUseCase.execute`` and will FAIL until those bugs are fixed:

* ``test_records_actor_as_requested_by`` — ``user`` is shadowed inside the
  permissions loop and the wrong UUID lands in the parallel operation.
* ``test_sibling_mode_falls_back_to_parent_when_item_is_only_non_collection_sibling``
  — ``switch_to`` is set to the item being deleted.
* ``test_decrements_known_tags_for_descendants_own_permission_users`` —
  the code reads ``item.permissions`` instead of ``member.permissions``,
  missing decrements for users that only see a descendant.
"""

import uuid

import pytest
import sqlalchemy as sa

from omoide import exceptions
from omoide import models
from omoide.database import db_models
from omoide.omoide_api.items.item_use_cases import DeleteItemUseCase


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

    async def test_anonymous_user_is_rejected(self, items_mediator):
        use_case = DeleteItemUseCase(items_mediator)
        with pytest.raises(exceptions.AccessDeniedError):
            await use_case.execute(
                user=models.User.new_anon(),
                item_uuid=uuid.uuid4(),
                desired_switch='parent',
            )

    async def test_unknown_item_uuid_raises(self, items_mediator, make_user_model):
        actor = await make_user_model()
        use_case = DeleteItemUseCase(items_mediator)
        with pytest.raises(exceptions.DoesNotExistError):
            await use_case.execute(
                user=actor,
                item_uuid=uuid.uuid4(),
                desired_switch='parent',
            )

    async def test_non_owner_is_rejected(
        self,
        items_mediator,
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

        use_case = DeleteItemUseCase(items_mediator)
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
        items_mediator,
        engine,
        make_user_model,
        make_item_model,
        make_metainfo,
    ):
        owner = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        make_metainfo(root.id)

        use_case = DeleteItemUseCase(items_mediator)
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
        items_mediator,
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

        await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert _read_item_status(engine, child.id) == models.Status.DELETED.value

    async def test_marks_metainfo_as_deleted(
        self,
        items_mediator,
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

        await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert _read_metainfo_deleted_at(engine, child.id) is not None

    async def test_clears_computed_tags(
        self,
        items_mediator,
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

        await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert _read_computed_tags(engine, child.id) == []

    async def test_decrements_owner_known_tags(
        self,
        items_mediator,
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

        await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert _read_known_tags_user_counter(engine, owner.id, 'red') == 4

    async def test_decrements_anon_known_tags_when_owner_is_public(
        self,
        items_mediator,
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

        await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert _read_known_tags_anon_counter(engine, 'red') == 6

    async def test_does_not_touch_anon_tags_when_owner_is_private(
        self,
        items_mediator,
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

        await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert _read_known_tags_anon_counter(engine, 'red') == 7

    async def test_decrements_known_tags_for_permission_user(
        self,
        items_mediator,
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

        await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert _read_known_tags_user_counter(engine, permitted.id, 'red') == 2


class TestDeleteItemUseCaseSwitchTo:
    """Verify the returned navigation target."""

    async def test_parent_mode_returns_parent(
        self,
        items_mediator,
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

        switch_to = await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert switch_to is not None
        assert switch_to.id == root.id

    async def test_sibling_mode_returns_next_sibling(
        self,
        items_mediator,
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

        switch_to = await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=sibling_b.uuid,
            desired_switch='sibling',
        )

        assert switch_to is not None
        assert switch_to.id == sibling_c.id

    async def test_sibling_mode_returns_previous_when_at_end(
        self,
        items_mediator,
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

        switch_to = await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=sibling_b.uuid,
            desired_switch='sibling',
        )

        assert switch_to is not None
        assert switch_to.id == sibling_a.id

    async def test_sibling_mode_falls_back_to_parent_for_collection_item(
        self,
        items_mediator,
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

        switch_to = await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=collection.uuid,
            desired_switch='sibling',
        )

        assert switch_to is not None
        assert switch_to.id == root.id

    async def test_sibling_mode_falls_back_to_parent_when_item_is_only_non_collection_sibling(
        self,
        items_mediator,
        make_user_model,
        make_item_model,
        make_metainfo,
    ):
        """Regression: ``siblings[0]`` is the item being deleted.

        When the only non-collection sibling is the item itself, the
        current implementation returns that (now soft-deleted) item. The
        correct behavior is to fall back to the parent. This test fails
        against the current code.
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

        switch_to = await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=lonely.uuid,
            desired_switch='sibling',
        )

        assert switch_to is not None
        assert switch_to.id != lonely.id, 'switch_to must not be the item that was just deleted'
        assert switch_to.id == root.id


class TestDeleteItemUseCaseObjectStorage:
    """Parallel operations emitted for object storage cleanup."""

    async def test_emits_parallel_operation_per_media_type(
        self,
        items_mediator,
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
            content_ext='jpg',
            preview_ext='jpg',
            thumbnail_ext='jpg',
        )
        make_metainfo(child.id)

        await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        ops = _read_parallel_ops(engine, name='soft_delete')
        media_types = sorted(op['media_type'] for op in ops)
        assert media_types == sorted(['content', 'preview', 'thumbnail'])

    async def test_no_parallel_operation_when_no_media(
        self,
        items_mediator,
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

        await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        assert _read_parallel_ops(engine, name='soft_delete') == []

    async def test_records_actor_as_requested_by(
        self,
        items_mediator,
        engine,
        make_user_model,
        make_item_model,
        make_metainfo,
    ):
        """Regression: actor is shadowed inside the permissions loop.

        ``extras['requested_by']`` is the audit trail for who initiated
        the deletion. The current implementation overwrites the local
        ``user`` variable while decrementing known_tags for permission
        holders, then passes that (wrong) value to
        ``object_storage.soft_delete``. This test fails against the
        current code; the recorded UUID is the last permission holder
        instead of the owner who actually performed the delete.
        """
        owner = await make_user_model()
        permitted = await make_user_model()
        root = await make_item_model(owner_id=owner.id, owner_uuid=owner.uuid)
        child = await make_item_model(
            owner_id=owner.id,
            owner_uuid=owner.uuid,
            parent_id=root.id,
            parent_uuid=root.uuid,
            content_ext='jpg',
            permissions=[permitted.id],
        )
        make_metainfo(child.id)

        await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=child.uuid,
            desired_switch='parent',
        )

        ops = _read_parallel_ops(engine, name='soft_delete')
        assert len(ops) == 1
        assert ops[0]['requested_by'] == str(owner.uuid), (
            'requested_by must be the actor, not a permission holder'
        )


class TestDeleteItemUseCaseCascade:
    """Family-wide effects: descendants get the same treatment as the root of the delete."""

    async def test_soft_deletes_all_descendants(
        self,
        items_mediator,
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

        await DeleteItemUseCase(items_mediator).execute(
            user=owner,
            item_uuid=parent.uuid,
            desired_switch='parent',
        )

        for item_id in (parent.id, grand_child_a.id, grand_child_b.id):
            assert _read_item_status(engine, item_id) == models.Status.DELETED.value
            assert _read_metainfo_deleted_at(engine, item_id) is not None

    async def test_decrements_known_tags_for_descendants_own_permission_users(
        self,
        items_mediator,
        engine,
        make_user_model,
        make_item_model,
        make_metainfo,
        set_computed_tags,
        set_known_tags_user,
    ):
        """Regression: ``item.permissions`` is used instead of ``member.permissions``.

        A descendant with its own permission user should have that user's
        ``known_tags`` counter decremented by the descendant's tags. The
        current implementation iterates the *root* item's permissions for
        every member, so a descendant-only permission holder is missed.
        This test fails against the current code.
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

        await DeleteItemUseCase(items_mediator).execute(
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
