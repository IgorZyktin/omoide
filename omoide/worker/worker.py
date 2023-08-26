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
        self._counter = 0

    @property
    def counter(self) -> int:
        """Return value of the operation counter."""
        return self._counter

    def download_media(self) -> None:
        """Download media from the database."""
        media_ids = self._database.get_media_ids(self._config.batch_size)
        LOG.debug('Got {} media records: {}', len(media_ids), media_ids)

        for media_id in media_ids:
            self._download_single_media(media_id)

    def _download_single_media(self, media_id: int) -> None:
        """Save single media record."""
        with self._database.start_session() as session:
            media = self._database.get_media(session, media_id)

            if media is None:
                return None

            if not media.ext or not media.content:
                return

            # noinspection PyBroadException
            try:
                self._download_media_content(media)
                self._alter_item_corresponding_to_media(media)
            except Exception:
                media.error = traceback.format_exc()
                LOG.exception('Failed to download media {}', media_id)

            media.processed_at = utils.now()
            session.commit()

    def _download_media_content(
            self,
            media: db_models.Media,
    ) -> None:
        """Save content for media as files."""
        for folder in self._get_folders():
            path = self._filesystem.ensure_folder_exists(
                folder,
                media.target_folder,
                str(media.owner_uuid),
                str(media.item_uuid)[:self._config.prefix_size],
            )
            filename = f'{media.item_uuid}.{media.ext or ""}'
            self._filesystem.safely_save(path, filename, media.content)

    @staticmethod
    def _alter_item_corresponding_to_media(media: db_models.Media) -> None:
        """Store changes in item description."""
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
                        command.processed_at = utils.now()
                        last_seen = command.id

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
