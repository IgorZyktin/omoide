"""Worker class."""

import hashlib
from pathlib import Path
import traceback
import zlib

from PIL import Image
import pyexiv2
import python_utilz as pu

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide.database import db_models
from omoide.omoide_worker import interfaces
from omoide.omoide_worker.database import WorkerDatabase
from omoide.omoide_worker.filesystem import Filesystem
from omoide.omoide_worker.worker_config import Config

LOG = custom_logging.get_logger(__name__)


class Worker(interfaces.AbsWorker):
    """Worker class."""

    def __init__(
        self,
        config: Config,
        database: WorkerDatabase,
        filesystem: Filesystem,
    ) -> None:
        """Initialize instance."""
        self._config = config
        self._database = database
        self._filesystem = filesystem
        self.counter = 0

    def download_media(self) -> None:
        """Download media from the database."""
        last_seen = None
        while True:
            with self._database.start_session():
                batch = self._database.get_media_batch(
                    self._config.batch_size,
                    last_seen,
                )

                if not batch:
                    self._database.session.commit()
                    return

                LOG.info('Got {} media records to download', len(batch))

                for media in batch:
                    # noinspection PyBroadException
                    try:
                        self._download_single_media(media)
                    except Exception:
                        LOG.exception(
                            'Failed to download media {}',
                            media.id,
                        )
                        media.error = traceback.format_exc()
                    finally:
                        self.counter += 1
                        media.processed_at = pu.now()
                        last_seen = media.id

                self._database.session.commit()
                if len(batch) < self._config.batch_size:
                    break

    def _download_single_media(self, media: db_models.Media) -> None:
        """Save single media record."""
        paths = self._filesystem.save_binary(
            owner_uuid=media.owner.uuid,
            item_uuid=media.item.uuid,
            media_type=media.media_type,
            ext=media.ext,
            content=media.content,
        )

        width = None
        height = None

        if paths:
            width, height = self._get_image_dimensions(paths[0])

        self._save_md5_signature(media)
        self._save_cr32_signature(media)
        self._save_exif(media)
        self._alter_item_corresponding_to_media(media, width, height)

    @staticmethod
    def _get_image_dimensions(path: Path) -> tuple[int, int] | tuple[None, None]:
        """Calculate width and height."""
        try:
            size = Image.open(path).size
        except FileNotFoundError:
            return None, None
        else:
            width, height = size

        return width, height

    @staticmethod
    def _alter_item_corresponding_to_media(
        media: db_models.Media,
        width: int | None,
        height: int | None,
    ) -> None:
        """Store changes in item description."""
        if media.media_type == const.CONTENT:
            media.item.metainfo.content_width = width
            media.item.metainfo.content_height = height
            media.item.content_ext = media.ext
            media.item.metainfo.content_size = len(media.content)

        elif media.media_type == const.PREVIEW:
            media.item.metainfo.preview_width = width
            media.item.metainfo.preview_height = height
            media.item.preview_ext = media.ext
            media.item.metainfo.preview_size = len(media.content)

        elif media.media_type == const.THUMBNAIL:
            media.item.metainfo.thumbnail_width = width
            media.item.metainfo.thumbnail_height = height
            media.item.thumbnail_ext = media.ext
            media.item.metainfo.thumbnail_size = len(media.content)

        else:
            msg = f'Got unknown media_type {media.media_type} for media {media.id}'
            raise ValueError(msg)

        media.item.metainfo.updated_at = pu.now()
        media.item.status = models.Status.AVAILABLE

    def _save_md5_signature(self, media: db_models.Media) -> None:
        """Save signature."""
        signature = db_models.SignatureMD5(
            item_id=media.item.id,
            signature=hashlib.md5(media.content).hexdigest(),
        )
        self._database.session.merge(signature)
        self._database.session.commit()

    def _save_cr32_signature(self, media: db_models.Media) -> None:
        """Save signature."""
        signature = db_models.SignatureCRC32(
            item_id=media.item.id,
            signature=zlib.crc32(media.content),
        )
        self._database.session.merge(signature)
        self._database.session.commit()

    def _save_exif(
        self,
        media: db_models.Media,
        encodings: tuple[str, ...] = ('utf-8', 'cp1251'),
    ) -> None:
        """Save EXIF info."""
        if media.media_type != const.CONTENT:
            return

        for encoding in encodings:
            try:
                with pyexiv2.ImageData(media.content) as img:
                    data = img.read_exif(encoding=encoding)
            except UnicodeDecodeError:
                LOG.exception(
                    'Failed to decode EXIF for media id={}, item_id={} because of unknown encoding',
                    media.id,
                    media.item_id,
                )
            except Exception:
                LOG.exception(
                    'Unexpectedly failed to decode EXIF for media id={}, item_id={}',
                    media.id,
                    media.item_id,
                )
                raise
            else:
                if data:
                    exif = db_models.EXIF(item_id=media.item.id, exif=data)
                    self._database.session.merge(exif)
                    self._database.session.commit()
                return

        problem = db_models.Problem(
            created_at=pu.now(),
            message='Failed all known encodings to process EXIF',
            extras={
                'media_id': media.id,
                'item_id': media.item_id,
            },
        )
        self._database.session.merge(problem)
        self._database.session.commit()

    def drop_media(self) -> None:
        """Delete media from the database."""
        dropped = self._database.drop_media()
        self.counter += dropped

        if dropped:
            LOG.debug('Dropped {} rows with media', dropped)

    def copy(self) -> None:
        """Perform manual copy operations."""
        last_seen = None
        while True:
            with self._database.start_session():
                batch = self._database.get_copies_batch(
                    self._config.batch_size,
                    last_seen,
                )

                LOG.debug('Got {} images to copy', len(batch))
                for command in batch:
                    # noinspection PyBroadException
                    try:
                        self._copy(command)
                    except Exception:
                        LOG.exception(
                            'Failed to copy image for command {}',
                            command.id,
                        )
                        command.error = traceback.format_exc()
                    finally:
                        self.counter += 1
                        command.processed_at = pu.now()
                        last_seen = command.id

                self._database.session.commit()
                if len(batch) < self._config.batch_size:
                    break

    def _copy(self, command: db_models.CommandCopy) -> None:
        """Perform filesystem operation on copying."""
        content = self._filesystem.load_binary(
            owner_uuid=command.owner.uuid,
            item_uuid=command.source.uuid,
            media_type=command.media_type,
            ext=command.ext,
        )
        media = self._database.create_media_from_copy(command, content)
        self._database.session.add(media)
        self._database.copy_parameters(command, len(content))
        self._database.mark_origin(command)

    def drop_copies(self) -> None:
        """Delete copy operations from the DB."""
        dropped = self._database.drop_copies()
        self.counter += dropped

        if dropped:
            LOG.debug('Dropped {} rows with copy commands', dropped)
