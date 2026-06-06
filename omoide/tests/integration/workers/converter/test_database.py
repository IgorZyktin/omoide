"""Tests for ``ConverterPostgreSQLDatabase``.

These tests target the data-access layer of the converter worker — every
method that touches ``queue_input_media`` / ``queue_output_media`` and the
OID refcount logic that the worker depends on for the shared-large-object
deletion path.
"""

from datetime import datetime
from datetime import timezone

import pytest
import sqlalchemy as sa

from omoide import const
from omoide.database import db_models
from omoide.workers.converter.database import ConverterPostgreSQLDatabase


@pytest.fixture
def db(test_db_url: str, engine):
    """Return a connected ``ConverterPostgreSQLDatabase``.

    ``engine`` is requested only to make sure the schema-clean fixture
    runs before this one — the worker's DB object opens its own engine.
    """
    _ = engine
    instance = ConverterPostgreSQLDatabase(url=test_db_url, echo=False)
    yield instance
    instance.disconnect()


# --- is_oid_referenced_elsewhere ----------------------------------------


class TestIsOidReferencedElsewhere:
    """The OID refcount check that gates large-object deletion."""

    def test_true_when_another_row_references_same_oid(
        self, db, insert_input_media, user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        first = insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid, oid=12345)
        second = insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid, oid=12345)

        assert db.is_oid_referenced_elsewhere(12345, exclude_id=first) is True
        assert db.is_oid_referenced_elsewhere(12345, exclude_id=second) is True

    def test_false_when_only_excluded_row_references_oid(
        self, db, insert_input_media, user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        only = insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid, oid=12345)

        assert db.is_oid_referenced_elsewhere(12345, exclude_id=only) is False

    def test_false_when_oid_is_unknown(
        self, db, insert_input_media, user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        row = insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid, oid=12345)

        assert db.is_oid_referenced_elsewhere(99999, exclude_id=row) is False

    def test_ignores_rows_with_null_oid(
        self, db, insert_input_media, user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        target = insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid, oid=12345)
        insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid, oid=None)
        insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid, oid=None)

        assert db.is_oid_referenced_elsewhere(12345, exclude_id=target) is False


# --- get_input_media_candidates -----------------------------------------


class TestGetInputMediaCandidates:
    """Polling query that drives the worker loop."""

    def test_returns_only_rows_with_matching_content_type(
        self, db, insert_input_media, user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        match = insert_input_media(
            user_uuid=user_uuid, item_uuid=item_uuid, content_type='image/jpeg',
        )
        insert_input_media(
            user_uuid=user_uuid, item_uuid=item_uuid, content_type='application/pdf',
        )

        candidates = db.get_input_media_candidates(batch_size=10, content_types=['image/jpeg'])

        assert candidates == [match]

    def test_excludes_locked_rows(self, db, insert_input_media, user_and_item):
        user_uuid, item_uuid = user_and_item
        free = insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid)
        insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid, lock='other-worker')

        candidates = db.get_input_media_candidates(batch_size=10, content_types=['image/jpeg'])

        assert candidates == [free]

    def test_excludes_rows_with_errors(self, db, insert_input_media, user_and_item):
        user_uuid, item_uuid = user_and_item
        clean = insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid)
        insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid, error='boom')

        candidates = db.get_input_media_candidates(batch_size=10, content_types=['image/jpeg'])

        assert candidates == [clean]

    def test_orders_by_id_and_respects_batch_size(
        self, db, insert_input_media, user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        first = insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid)
        second = insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid)
        insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid)

        candidates = db.get_input_media_candidates(batch_size=2, content_types=['image/jpeg'])

        assert candidates == [first, second]


# --- lock_input_media ---------------------------------------------------


class TestLockInputMedia:
    """The acquire-lock-or-skip primitive used by the worker."""

    def test_locks_an_unlocked_row(self, db, engine, insert_input_media, user_and_item):
        user_uuid, item_uuid = user_and_item
        row_id = insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid)

        assert db.lock_input_media(row_id, 'worker-1') is True

        with engine.connect() as conn:
            lock = conn.execute(
                sa.select(db_models.QueueInputMedia.lock).where(
                    db_models.QueueInputMedia.id == row_id
                )
            ).scalar_one()
        assert lock == 'worker-1'

    def test_does_not_lock_already_locked_row(
        self, db, insert_input_media, user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        row_id = insert_input_media(
            user_uuid=user_uuid, item_uuid=item_uuid, lock='someone-else',
        )

        assert db.lock_input_media(row_id, 'worker-1') is False


# --- get_input_media ----------------------------------------------------


class TestGetInputMedia:
    def test_returns_full_input_media_model(
        self, db, insert_input_media, user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        row_id = insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=b'hello',
            ext='png',
            content_type='image/png',
            oid=42,
        )

        model = db.get_input_media(row_id)

        assert model.id == row_id
        assert model.user_uuid == user_uuid
        assert model.item_uuid == item_uuid
        assert model.content == b'hello'
        assert model.ext == 'png'
        assert model.content_type == 'image/png'
        assert model.extras['oid'] == 42
        assert model.error is None


# --- save_output_media --------------------------------------------------


class TestSaveOutputMedia:
    def test_small_content_stays_in_bytea_and_sets_oid_none(
        self, db, engine, user_and_item,
    ):
        from omoide import models

        user_uuid, item_uuid = user_and_item
        payload = b'\x89PNG\r\n' + b'x' * 100
        model = models.InputMedia(
            id=-1,
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            created_at=datetime.now(timezone.utc),
            ext='jpg',
            content_type='image/jpeg',
            extras={'extract_exif': False, 'oid': 9999},
            error=None,
            content=payload,
        )

        db.save_output_media(model, media_type='thumbnail')

        with engine.connect() as conn:
            row = conn.execute(
                sa.select(db_models.QueueOutputMedia).where(
                    db_models.QueueOutputMedia.item_uuid == item_uuid
                )
            ).one()
        assert row.media_type == 'thumbnail'
        assert row.content == payload
        # save_output_media REPLACES the input oid with the output oid (None for small content).
        assert row.extras['oid'] is None
        assert model.extras['oid'] is None

    def test_large_content_creates_large_object_and_clears_bytea(
        self, db, engine, large_payload, user_and_item,
    ):
        from omoide import models

        user_uuid, item_uuid = user_and_item
        model = models.InputMedia(
            id=-1,
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            created_at=datetime.now(timezone.utc),
            ext='jpg',
            content_type='image/jpeg',
            extras={'extract_exif': False, 'oid': None},
            error=None,
            content=large_payload,
        )

        db.save_output_media(model, media_type='content')

        with engine.connect() as conn:
            row = conn.execute(
                sa.select(db_models.QueueOutputMedia).where(
                    db_models.QueueOutputMedia.item_uuid == item_uuid
                )
            ).one()
        assert row.content == b''
        assert isinstance(row.extras['oid'], int)
        assert row.extras['oid'] > 0
        # the bytes round-trip through Postgres large object storage
        roundtrip = db.get_large_object(row.extras['oid'])
        assert roundtrip == large_payload


# --- delete_media / mark_failed_and_release_lock ------------------------


class TestDeleteMedia:
    def test_removes_row(self, db, engine, insert_input_media, user_and_item):
        user_uuid, item_uuid = user_and_item
        row_id = insert_input_media(user_uuid=user_uuid, item_uuid=item_uuid)

        db.delete_media(row_id)

        with engine.connect() as conn:
            remaining = conn.execute(
                sa.select(sa.func.count())
                .select_from(db_models.QueueInputMedia)
                .where(db_models.QueueInputMedia.id == row_id)
            ).scalar_one()
        assert remaining == 0


class TestMarkFailedAndReleaseLock:
    def test_clears_lock_and_sets_error(
        self, db, engine, insert_input_media, user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        row_id = insert_input_media(
            user_uuid=user_uuid, item_uuid=item_uuid, lock='worker-1',
        )

        db.mark_failed_and_release_lock(row_id, error='conversion failed')

        with engine.connect() as conn:
            row = conn.execute(
                sa.select(
                    db_models.QueueInputMedia.lock,
                    db_models.QueueInputMedia.error,
                ).where(db_models.QueueInputMedia.id == row_id)
            ).one()
        assert row.lock is None
        assert row.error == 'conversion failed'


# --- large object round-trip via base class -----------------------------


class TestLargeObjectRoundtrip:
    """Sanity test on the inherited base class methods."""

    def test_save_then_get(self, db):
        payload = b'binary-payload-' + b'\xff' * 1000
        oid = db.save_large_object(payload)
        try:
            assert db.get_large_object(oid) == payload
        finally:
            db.delete_large_object(oid)

    def test_delete_removes_large_object(self, db, engine):
        payload = b'transient-' + b'x' * (const.MEGABYTE // 2)
        oid = db.save_large_object(payload)
        db.delete_large_object(oid)

        with engine.connect() as conn:
            still_there = conn.execute(
                sa.text('SELECT 1 FROM pg_largeobject_metadata WHERE oid = :oid'),
                {'oid': oid},
            ).scalar()
        assert still_there is None
