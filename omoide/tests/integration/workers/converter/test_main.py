"""Tests for the converter worker's ``do_work`` loop.

These tests exercise the full converter cycle against a real Postgres
instance: enqueue an input row, run ``do_work``, assert that the row was
processed, output rows were produced, and the large-object lifecycle is
correct (especially the recently-added refcount path).
"""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image
import pytest
import sqlalchemy as sa

from omoide import const
from omoide.database import db_models
from omoide.workers.common import metrics as common_metrics
from omoide.workers.converter import __main__ as converter_main
from omoide.workers.converter.database import ConverterPostgreSQLDatabase


def _make_jpeg(size: tuple[int, int] = (200, 200), color: str = 'red') -> bytes:
    """Encode a small in-memory JPEG."""
    buf = BytesIO()
    Image.new('RGB', size, color=color).save(buf, format='JPEG', quality=80)
    return buf.getvalue()


def _make_png(size: tuple[int, int] = (200, 200)) -> bytes:
    buf = BytesIO()
    Image.new('RGB', size, color='blue').save(buf, format='PNG')
    return buf.getvalue()


def _make_webp(size: tuple[int, int] = (200, 200)) -> bytes:
    buf = BytesIO()
    Image.new('RGB', size, color='green').save(buf, format='WEBP', quality=80)
    return buf.getvalue()


@dataclass
class _StubConfig:
    """Minimal config carrying the fields that ``do_work`` reads."""

    temp_folder: Path
    name: str = 'converter-test'
    input_batch: int = 10


@pytest.fixture
def db(test_db_url: str, engine):
    """Connect converter DB.

    ``engine`` ordering ensures schema-clean first.
    """
    _ = engine
    instance = ConverterPostgreSQLDatabase(url=test_db_url, echo=False)
    yield instance
    instance.disconnect()


@pytest.fixture
def config(converter_temp_folder: Path) -> _StubConfig:
    return _StubConfig(temp_folder=converter_temp_folder)


def _count(engine, table) -> int:
    with engine.connect() as conn:
        return int(conn.execute(sa.select(sa.func.count()).select_from(table)).scalar_one())


def _large_object_exists(engine, oid: int) -> bool:
    with engine.connect() as conn:
        row = conn.execute(
            sa.text('SELECT 1 FROM pg_largeobject_metadata WHERE oid = :oid'),
            {'oid': oid},
        ).scalar()
    return row is not None


# --- empty queue --------------------------------------------------------


class TestEmptyQueue:
    def test_returns_false_when_no_candidates(self, db, config, metrics_collector):
        assert converter_main.do_work(config, db, metrics_collector) is False


# --- happy path: small image, no OID ------------------------------------


class TestSmallImageNoOid:
    def test_processes_and_removes_input_row(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_jpeg(),
            content_type='image/jpeg',
            ext='jpg',
            oid=None,
        )

        result = converter_main.do_work(config, db, metrics_collector)

        assert result is True
        assert _count(engine, db_models.QueueInputMedia) == 0
        # Image converter emits content + preview + thumbnail (3 rows)
        assert _count(engine, db_models.QueueOutputMedia) == 3

    def test_increments_metrics(
        self,
        db,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_jpeg(),
            content_type='image/jpeg',
        )

        converter_main.do_work(config, db, metrics_collector)

        assert metrics_collector.get_value(common_metrics.FILES_PROCESSED) == 1.0
        assert metrics_collector.get_value(common_metrics.ERRORS) == 0.0


# --- skip_content / skip_preview ----------------------------------------


class TestSkipFlags:
    def test_skip_content_and_skip_preview_emits_only_thumbnail(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        """Mirrors what the upload use case emits for the parent item."""
        user_uuid, item_uuid = user_and_item
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_jpeg(),
            content_type='image/jpeg',
            extras={'skip_content': True, 'skip_preview': True},
        )

        assert converter_main.do_work(config, db, metrics_collector) is True

        with engine.connect() as conn:
            media_types = [
                row[0] for row in conn.execute(sa.select(db_models.QueueOutputMedia.media_type))
            ]
        assert media_types == ['thumbnail']


# --- happy path: large image with OID -----------------------------------


class TestLargeImageWithOid:
    """OID is alive at start of conversion, deleted afterwards when nobody else refs it."""

    def test_solo_oid_is_deleted_after_processing(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        # Real JPEG content goes into a large object; the BYTEA stays empty.
        payload = _make_jpeg(size=(400, 400))
        oid = db.save_large_object(payload)
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=b'',
            content_type='image/jpeg',
            oid=oid,
        )

        assert converter_main.do_work(config, db, metrics_collector) is True

        assert _count(engine, db_models.QueueInputMedia) == 0
        assert _large_object_exists(engine, oid) is False


# --- shared OID lifecycle (the recent change) ---------------------------


class TestSharedOidLifecycle:
    """The refcount path on ``__main__.py`` lines 139-146.

    Two queue rows reference the same OID — the converter must keep the
    OID alive until BOTH rows are processed, then delete it.
    """

    def test_first_pass_keeps_oid_alive_when_other_row_still_references_it(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        payload = _make_jpeg(size=(300, 300))
        oid = db.save_large_object(payload)

        # Child entry (full conversion).
        child_id = insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=b'',
            content_type='image/jpeg',
            oid=oid,
        )
        # Parent entry (thumbnail only) — references the same OID.
        parent_id = insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=b'',
            content_type='image/jpeg',
            oid=oid,
            extras={'skip_content': True, 'skip_preview': True},
        )

        # First call processes the lower-id row (child).
        assert converter_main.do_work(config, db, metrics_collector) is True

        with engine.connect() as conn:
            remaining = [row[0] for row in conn.execute(sa.select(db_models.QueueInputMedia.id))]
        assert remaining == [parent_id]
        # Child is done, parent still references the OID — OID MUST be alive.
        assert _large_object_exists(engine, oid) is True
        # avoid an "unused variable" complaint in the assertion narrative
        assert child_id not in remaining

    def test_second_pass_deletes_oid_when_no_more_references(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        payload = _make_jpeg(size=(300, 300))
        oid = db.save_large_object(payload)
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=b'',
            content_type='image/jpeg',
            oid=oid,
        )
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=b'',
            content_type='image/jpeg',
            oid=oid,
            extras={'skip_content': True, 'skip_preview': True},
        )

        assert converter_main.do_work(config, db, metrics_collector) is True
        # OID stays alive after the first pass.
        assert _large_object_exists(engine, oid) is True

        assert converter_main.do_work(config, db, metrics_collector) is True

        assert _count(engine, db_models.QueueInputMedia) == 0
        # Last consumer is responsible for the unlink.
        assert _large_object_exists(engine, oid) is False


# --- failure path -------------------------------------------------------


class TestConversionFailure:
    def test_corrupt_content_marks_row_failed_and_keeps_oid_alive(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        payload = b'not-a-real-image-just-some-bytes'
        oid = db.save_large_object(payload)
        row_id = insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=b'',
            content_type='image/jpeg',
            oid=oid,
        )

        result = converter_main.do_work(config, db, metrics_collector)

        assert result is False
        with engine.connect() as conn:
            row = conn.execute(
                sa.select(
                    db_models.QueueInputMedia.lock,
                    db_models.QueueInputMedia.error,
                ).where(db_models.QueueInputMedia.id == row_id)
            ).one()
        assert row.lock is None
        assert row.error
        assert row.error != ''
        # OID must survive so a retry path can read the content again.
        assert _large_object_exists(engine, oid) is True
        assert metrics_collector.get_value(common_metrics.ERRORS) == 1.0


# --- unsupported content type filtering ---------------------------------


class TestUnsupportedContentType:
    def test_rows_with_unsupported_content_type_are_not_picked_up(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_jpeg(),
            content_type='application/octet-stream',
        )

        assert converter_main.do_work(config, db, metrics_collector) is False
        assert _count(engine, db_models.QueueInputMedia) == 1


# --- PNG path -----------------------------------------------------------


class TestPng:
    def test_png_is_processed(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_png(),
            content_type='image/png',
            ext='png',
        )

        assert converter_main.do_work(config, db, metrics_collector) is True
        assert _count(engine, db_models.QueueOutputMedia) == 3


# --- ordering -----------------------------------------------------------


class TestProcessingOrder:
    def test_picks_lower_id_first(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        first = insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_jpeg(),
        )
        second = insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_jpeg(),
        )

        assert converter_main.do_work(config, db, metrics_collector) is True

        with engine.connect() as conn:
            remaining = [row[0] for row in conn.execute(sa.select(db_models.QueueInputMedia.id))]
        assert first not in remaining
        assert second in remaining


# --- WEBP ---------------------------------------------------------------


class TestWebp:
    def test_webp_is_processed(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_webp(),
            content_type='image/webp',
            ext='webp',
        )

        assert converter_main.do_work(config, db, metrics_collector) is True
        assert _count(engine, db_models.QueueOutputMedia) == 3


# --- output media format / dimensions -----------------------------------


def _outputs(engine) -> dict[str, db_models.QueueOutputMedia]:
    """Return queue_output_media rows keyed by media_type."""
    with engine.connect() as conn:
        rows = conn.execute(sa.select(db_models.QueueOutputMedia)).all()
    return {row.media_type: row for row in rows}


class TestOutputMediaTypes:
    def test_emits_content_preview_and_thumbnail(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_jpeg(),
            content_type='image/jpeg',
        )

        converter_main.do_work(config, db, metrics_collector)

        assert set(_outputs(engine)) == {'content', 'preview', 'thumbnail'}


class TestOutputFormats:
    def test_preview_and_thumbnail_are_jpeg_regardless_of_input(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_png(),
            content_type='image/png',
            ext='png',
        )

        converter_main.do_work(config, db, metrics_collector)

        outputs = _outputs(engine)
        assert outputs['preview'].ext == 'jpg'
        assert outputs['preview'].content_type == 'image/jpeg'
        assert outputs['thumbnail'].ext == 'jpg'
        assert outputs['thumbnail'].content_type == 'image/jpeg'

    def test_content_keeps_original_format(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_png(),
            content_type='image/png',
            ext='png',
        )

        converter_main.do_work(config, db, metrics_collector)

        outputs = _outputs(engine)
        assert outputs['content'].ext == 'png'
        assert outputs['content'].content_type == 'image/png'


class TestOutputDimensions:
    def test_thumbnail_and_preview_are_within_their_size_limits(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        # 2000 px on the long side — large enough to be downscaled for both
        # preview (1024) and thumbnail (384).
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_jpeg(size=(2000, 1000)),
            content_type='image/jpeg',
        )

        converter_main.do_work(config, db, metrics_collector)

        outputs = _outputs(engine)
        with Image.open(BytesIO(outputs['preview'].content)) as img:
            preview_size = img.size
        with Image.open(BytesIO(outputs['thumbnail'].content)) as img:
            thumb_size = img.size
        assert max(preview_size) <= const.PREVIEW_SIZE
        assert max(thumb_size) <= const.THUMBNAIL_SIZE
        # Aspect ratio is preserved (2:1).
        assert preview_size[0] // preview_size[1] == 2
        assert thumb_size[0] // thumb_size[1] == 2

    def test_small_image_is_not_upscaled(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        # 100x100 is smaller than both thumbnail (384) and preview (1024).
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_jpeg(size=(100, 100)),
            content_type='image/jpeg',
        )

        converter_main.do_work(config, db, metrics_collector)

        outputs = _outputs(engine)
        with Image.open(BytesIO(outputs['preview'].content)) as img:
            assert img.size == (100, 100)
        with Image.open(BytesIO(outputs['thumbnail'].content)) as img:
            assert img.size == (100, 100)


# --- skip flag variants -------------------------------------------------


class TestSkipContentOnly:
    def test_skip_content_emits_preview_and_thumbnail(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_jpeg(),
            content_type='image/jpeg',
            extras={'skip_content': True},
        )

        assert converter_main.do_work(config, db, metrics_collector) is True
        assert set(_outputs(engine)) == {'preview', 'thumbnail'}


# --- retry behavior after a failure -------------------------------------


class TestFailedRowIsNotRetried:
    def test_second_do_work_finds_no_candidates_after_failure(
        self,
        db,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=b'garbage',
            content_type='image/jpeg',
        )

        assert converter_main.do_work(config, db, metrics_collector) is False
        # The row stays in the queue with `error` set — the candidates query
        # filters it out, so the next worker tick is a no-op.
        assert converter_main.do_work(config, db, metrics_collector) is False


# --- batching: do_work processes one candidate per call ----------------


class TestBatchSingleCandidatePerCall:
    def test_only_one_row_processed_per_do_work_invocation(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        for _ in range(3):
            insert_input_media(
                user_uuid=user_uuid,
                item_uuid=item_uuid,
                content=_make_jpeg(),
                content_type='image/jpeg',
            )

        assert converter_main.do_work(config, db, metrics_collector) is True

        # Two rows still queued; output table holds outputs for the first row only.
        assert _count(engine, db_models.QueueInputMedia) == 2
        assert _count(engine, db_models.QueueOutputMedia) == 3


# --- lock-stealing path (the `continue` branch in do_work) --------------


class TestLockStealing:
    def test_continues_to_next_candidate_when_first_lock_fails(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
        monkeypatch,
    ):
        """The race covered by ``do_work``'s ``continue`` on failed lock.

        ``get_input_media_candidates`` returns rows whose ``lock`` was NULL at
        SELECT time. Between SELECT and UPDATE, another worker may have grabbed
        one. Simulating the race with monkeypatching is the only way to drive
        this branch in a single-process test.
        """
        user_uuid, item_uuid = user_and_item
        first = insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_jpeg(),
        )
        second = insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_jpeg(),
        )

        original_lock = db.lock_input_media

        def _flaky_lock(target_id: int, name: str) -> bool:
            if target_id == first:
                return False  # someone else got there first
            return original_lock(target_id, name)

        monkeypatch.setattr(db, 'lock_input_media', _flaky_lock)

        assert converter_main.do_work(config, db, metrics_collector) is True

        with engine.connect() as conn:
            remaining = sorted(
                row[0] for row in conn.execute(sa.select(db_models.QueueInputMedia.id))
            )
        # The first row was "stolen" — still there with no lock applied by us.
        # The second row was processed and removed.
        assert remaining == [first]
        assert second not in remaining


# --- extras propagate through to outputs --------------------------------


class TestExtrasPropagation:
    def test_extract_exif_flag_survives_into_output_extras(
        self,
        db,
        engine,
        config,
        metrics_collector,
        insert_input_media,
        user_and_item,
    ):
        user_uuid, item_uuid = user_and_item
        insert_input_media(
            user_uuid=user_uuid,
            item_uuid=item_uuid,
            content=_make_jpeg(),
            content_type='image/jpeg',
            extras={'extract_exif': True},
        )

        converter_main.do_work(config, db, metrics_collector)

        outputs = _outputs(engine)
        # ``extract_exif`` is a directive the downloader reads later — every
        # output row inherits it so the next stage knows what to do.
        for row in outputs.values():
            assert row.extras.get('extract_exif') is True
