"""Copy image between items."""

import shutil
from typing import assert_never

from omoide import const
from omoide import custom_logging
from aiofiles.os import wrap
from omoide.database.implementations import impl_sqlalchemy
from omoide.infra.locators import FilesystemLocator
from omoide.workers.parallel.commands.base_command import Command
from omoide.workers.parallel.database import ParallelPostgreSQLDatabase
from omoide.models import ParallelCommand

LOG = custom_logging.get_logger(__name__)


class CopyImageCommand(Command):
    """Copy image between items."""

    def __init__(
        self,
        dto: ParallelCommand,
        database: ParallelPostgreSQLDatabase,
        users: impl_sqlalchemy.UsersRepo,
        items: impl_sqlalchemy.ItemsRepo,
        meta: impl_sqlalchemy.MetaRepo,
        locator: FilesystemLocator,
    ) -> None:
        """Initialize instance."""
        super().__init__(dto)
        self.database = database
        self.users = users
        self.items = items
        self.meta = meta
        self.locator = locator

    async def execute(self) -> tuple[list[str], int]:
        """Start execution of the command."""
        source_item_id = self.dto.source_item_id
        target_item_id = self.dto.target_item_id
        including_content = self.dto.extras.get('including_content')
        including_video = self.dto.extras.get('including_video')

        async with self.database.transaction() as conn:
            source_item = await self.items.get_by_id(conn, source_item_id)
            source_owner = await self.users.get_by_id(
                conn, source_item.owner_id
            )

            target_item = await self.items.get_by_id(conn, target_item_id)
            target_owner = await self.users.get_by_id(
                conn, target_item.owner_id
            )

        async_copyfile = wrap(shutil.copyfile)
        media_types = [const.MediaType.PREVIEW, const.MediaType.THUMBNAIL]

        if including_content:
            media_types.append(const.MediaType.CONTENT)
        if including_video:
            media_types.append(const.MediaType.VIDEO)

        for media in media_types:
            source_segments = self.locator.get_path_segments(
                owner=source_owner,
                item=source_item,
                media_type=media,
            )

            if source_segments is None:
                msg = f'Item {source_item.uuid} does not have a {media}'
                raise ValueError(msg)

            _root, _media, _uuid, _prefix, _filename = source_segments
            source_path = _root / _media / _uuid / _prefix / _filename

            match media:
                case const.MediaType.VIDEO:
                    ext = source_item.content_ext
                case const.MediaType.CONTENT:
                    ext = source_item.content_ext
                case const.MediaType.PREVIEW:
                    ext = source_item.preview_ext
                case const.MediaType.THUMBNAIL:
                    ext = source_item.thumbnail_ext
                case _:
                    assert_never(media)
                    raise  # noqa: PLE0704

            new_prefix = self.locator.get_prefix(target_item)
            new_filename = self.locator.get_filename(target_item, ext)
            target_path = (
                _root
                / _media
                / str(target_owner.uuid)
                / new_prefix
                / new_filename
            )

            await async_copyfile(
                src=source_path,
                dst=target_path,
            )
            LOG.debug('Copied file: {} to {}', source_path, target_path)

        async with self.database.transaction() as conn:
            if including_content:
                target_item.content_ext = source_item.content_ext
            target_item.preview_ext = source_item.preview_ext
            target_item.thumbnail_ext = source_item.thumbnail_ext
            await self.items.save(conn, target_item)

            source_metainfo = await self.meta.get_by_item(conn, source_item)
            target_metainfo = await self.meta.get_by_item(conn, target_item)
            target_metainfo.copy_from(
                source_metainfo, including_content=including_content
            )

            await self.meta.save(conn, target_metainfo)
            await self.meta.add_item_note(
                conn=conn,
                item=target_item,
                key='copied_image_from',
                value=str(source_item.uuid),
            )

        return [], 0
