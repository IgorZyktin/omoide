"""Worker class.
"""
import traceback

from omoide import utils
from omoide.infra import custom_logging
from omoide.storage.database import db_models
from omoide.worker import interfaces
from omoide.worker.database import Database
from omoide.worker.filesystem import Filesystem
from omoide.worker.worker_config import Config

LOG = custom_logging.get_logger(__name__)


class Worker(interfaces.AbsWorker):
    """Worker class."""

    def __init__(
            self,
            config: Config,
            database: Database,
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

                LOG.debug('Got {} media records to download', len(batch))
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
            target_folder=media.target_folder,  # FIXME - alter to media_type
            ext=media.ext,
            content=media.content,
        )
        self._alter_item_corresponding_to_media(media)

    @staticmethod
    def _alter_item_corresponding_to_media(media: db_models.Media) -> None:
        """Store changes in item description."""
        # FIXME - alter to media_type
        if media.target_folder == 'content':
            media.item.content_ext = media.ext
            media.item.metainfo.content_size = len(media.content or b'')
        elif media.target_folder == 'preview':
            media.item.preview_ext = media.ext
            media.item.metainfo.preview_size = len(media.content or b'')
        else:
            media.item.thumbnail_ext = media.ext
            media.item.metainfo.thumbnail_size = len(media.content or b'')

        media.item.metainfo.updated_at = utils.now()

    def drop_media(self) -> None:
        """Delete media from the database."""
        dropped = self._database.drop_media()

        if dropped:
            LOG.debug('Dropped {} rows with media', dropped)

    def copy_thumbnails(self) -> None:
        """Perform manual thumbnail copy operations."""
        last_seen = None
        while True:
            with self._database.start_session():
                batch = self._database.get_thumbnail_batch(
                    self._config.batch_size,
                    last_seen,
                )

                LOG.debug('Got {} thumbnails to copy', len(batch))
                for command in batch:
                    # noinspection PyBroadException
                    try:
                        self._copy_thumbnail(command)
                    except Exception:
                        LOG.exception(
                            'Failed to copy thumbnail for command {}',
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

    def _copy_thumbnail(
            self,
            command: db_models.CommandCopyThumbnail,
    ) -> None:
        """Perform filesystem operation on copying."""
        content = self._filesystem.load_binary(
            owner_uuid=command.owner_uuid,
            item_uuid=command.source_uuid,
            target_folder='thumbnail',
            ext=command.ext,
        )
        media = self._database.create_media_from_copy(command, content)
        self._database.session.add(media)
        self._database.copy_thumbnail_parameters(command, len(content))
        self._database.mark_origin_of_thumbnail(command)

    def drop_thumbnail_copies(self) -> None:
        """Delete thumbnail copy operations from the DB."""
        dropped = self._database.drop_thumbnail_copies()

        if dropped:
            LOG.debug('Dropped {} rows with thumbnail copy commands', dropped)
