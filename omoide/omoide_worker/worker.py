"""Worker class."""

import traceback

from omoide import const
from omoide import utils
from omoide import custom_logging
from omoide.storage.database import db_models
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
                        media.processed_at = utils.now()
                        last_seen = media.id

                self._database.session.commit()
                if len(batch) < self._config.batch_size:
                    break

    def _download_single_media(self, media: db_models.Media) -> None:
        """Save single media record."""
        self._filesystem.save_binary(
            owner_uuid=media.owner_uuid,
            item_uuid=media.item_uuid,
            media_type=media.media_type,
            ext=media.ext,
            content=media.content,
        )
        self._alter_item_corresponding_to_media(media)

    @staticmethod
    def _alter_item_corresponding_to_media(media: db_models.Media) -> None:
        """Store changes in item description."""
        if media.media_type == const.CONTENT:
            media.item.content_ext = media.ext
            media.item.metainfo.content_size = len(media.content)

        elif media.media_type == const.PREVIEW:
            media.item.preview_ext = media.ext
            media.item.metainfo.preview_size = len(media.content)

        elif media.media_type == const.THUMBNAIL:
            media.item.thumbnail_ext = media.ext
            media.item.metainfo.thumbnail_size = len(media.content)

        else:
            msg = (
                f'Got unknown media_type {media.media_type} ' 
                f'for media {media.id}'
            )
            raise ValueError(msg)

        media.item.metainfo.updated_at = utils.now()

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
                        command.processed_at = utils.now()
                        last_seen = command.id

                self._database.session.commit()
                if len(batch) < self._config.batch_size:
                    break

    def _copy(self, command: db_models.CommandCopy) -> None:
        """Perform filesystem operation on copying."""
        content = self._filesystem.load_binary(
            owner_uuid=command.owner_uuid,
            item_uuid=command.source_uuid,
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
