"""Worker class.
"""
import traceback
from typing import Iterator

from sqlalchemy.orm.attributes import flag_modified

from omoide import utils
from omoide.daemons.worker import interfaces
from omoide.daemons.worker.database import Database
from omoide.daemons.worker.filesystem import Filesystem
from omoide.daemons.worker.worker_config import Config
from omoide.infra import custom_logging
from omoide.storage.database import models

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
        self.config = config
        self.database = database
        self.filesystem = filesystem

    def _get_folders(self) -> Iterator[str]:
        """Return all folders where we plan to save anything."""
        if self.config.save_hot:
            yield self.config.hot_folder
        if self.config.save_cold:
            yield self.config.cold_folder

    @property
    def _formula(self) -> dict[str, bool]:
        """Return formula of this worker."""
        return {
            f'{self.config.name}-hot': self.config.save_hot,
            f'{self.config.name}-cold': self.config.save_cold,
        }

    def download_media(self) -> None:
        """Download media from the database."""
        media_ids = self.database.get_media_ids(
            formula=self._formula,
            limit=self.config.batch_size,
        )

        LOG.debug('Got {} media records: {}', len(media_ids), media_ids)

        for media_id in media_ids:
            self._download_single_media(media_id)

    def _download_single_media(self, media_id: int) -> None:
        """Save single media record."""
        with self.database.start_session() as session:
            media = self.database.select_media(session, media_id)

            if media is None:
                return None

            # noinspection PyBroadException
            try:
                self._download_media_content(media)
                self._alter_item_corresponding_to_media(media)
            except Exception:
                media.error += '\n' + traceback.format_exc()
                LOG.exception('Failed to download media {}', media_id)
            else:
                media.replication.update(self._formula)
                flag_modified(media, 'replication')

            media.attempts = (media.attempts or 0) + 1
            media.processed_at = utils.now()

            session.commit()

    def _download_media_content(
            self,
            media: models.Media,
    ) -> None:
        """Save content for media as files."""
        if not media.ext or not media.content:
            return

        for folder in self._get_folders():
            path = self.filesystem.ensure_folder_exists(
                folder,
                media.target_folder,
                str(media.owner_uuid),
                str(media.item_uuid)[:self.config.prefix_size],
            )
            filename = f'{media.item_uuid}.{media.ext or ""}'
            self.filesystem.safely_save(path, filename, media.content)

    @staticmethod
    def _alter_item_corresponding_to_media(media: models.Media) -> None:
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
        LOG.debug('Dropping all media that fits into formula: {}',
                  self.config.replication_formula)

        dropped = self.database.drop_media(self.config.replication_formula)

        if dropped:
            LOG.debug('Dropped {} rows with media', dropped)

    def manual_copy(self) -> None:
        """Perform manual copy operations."""
        targets = self.database.get_manual_copy_targets(self.config.batch_size)
        LOG.debug('Got {} items to copy: {}', len(targets), targets)

        for copy_id in targets:
            self._process_single_copy(copy_id)

    def _process_single_copy(self, copy_id: int) -> None:
        """Perform filesystem operation on copying."""
        with self.database.start_session() as session:
            copy = self.database.select_copy_operation(session, copy_id)

            if copy is None:
                return

            # noinspection PyBroadException
            try:
                content = self._load_content_for_copy(copy)
                media = self.database.create_media_from_copy(copy,
                                                             content)
            except Exception:
                LOG.exception('Failed to load content for copy {}',
                              copy_id)
                copy.status = 'fail'
                copy.error += '\n' + traceback.format_exc()
                copy.processed_at = utils.now()
                session.commit()
                return

            session.add(media)

            # noinspection PyBroadException
            try:
                self.database.copy_content_parameters(
                    self.config, self.filesystem, session, copy)
                self.database.mark_origin(copy)
            except Exception:
                LOG.exception('Failed to save changes in copy {}', copy_id)
                copy.status = 'fail'
                copy.error += '\n' + traceback.format_exc()
                copy.processed_at = utils.now()
            else:
                copy.status = 'done'
                copy.processed_at = utils.now()

    def _load_content_for_copy(self, copy: models.ManualCopy) -> bytes:
        """Return binary data corresponding to this copy operation."""
        folder = self.config.hot_folder or self.config.cold_folder
        bucket = utils.get_bucket(copy.source_uuid, self.config.prefix_size)

        content = self.filesystem.load_from_filesystem(
            folder,
            str(copy.target_folder),
            str(copy.owner_uuid),
            bucket,
            f'{copy.source_uuid}.{(copy.ext or "").lower()}'
        )

        return content

    def drop_manual_copies(self) -> None:
        """Delete copy operations from the database."""
        dropped = self.database.drop_manual_copies()

        if dropped:
            LOG.debug('Dropped {} rows with manual copies', dropped)
