"""Add new image/video to the storage."""

import asyncio
import math
import os
from concurrent.futures import ProcessPoolExecutor
from contextlib import suppress
from pathlib import Path

import aiofiles
import aiofiles.os
import python_utilz as pu
from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps
from moviepy import VideoFileClip

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide.database.implementations import impl_sqlalchemy
from omoide.infra.locators import FilesystemLocator
from omoide.models import ParallelCommand
from omoide.object_storage.interfaces import AbsObjectStorage
from omoide.workers.parallel.commands.base_command import Command
from omoide.workers.parallel.database import ParallelPostgreSQLDatabase

LOG = custom_logging.get_logger(__name__)


def get_new_image_dimensions(
    old_width: int,
    old_height: int,
    new_size: int,
) -> tuple[int, int]:
    """Calculate new size while maintaining proportions."""
    if old_width >= old_height:
        new_width = float(min(old_width, new_size))
        coefficient = new_width / old_width
        new_height = old_height * coefficient
    else:
        new_height = min(old_height, new_size)
        coefficient = new_height / old_height
        new_width = old_width * coefficient

    return math.ceil(new_width), math.ceil(new_height)


def resize(img: Image.Image, size: int, dst_path: Path) -> tuple[int, int]:
    """Resize to given dimensions."""
    img = ImageOps.exif_transpose(img)
    old_width, old_height = img.size
    new_width, new_height = get_new_image_dimensions(
        old_width, old_height, size
    )
    new_img = img.resize((new_width, new_height))
    new_img = new_img.convert('RGB')
    new_img = new_img.filter(ImageFilter.SHARPEN)

    new_img.save(
        dst_path,
        'JPEG',
        quality=const.IMAGE_QUALITY,
        optimize=True,
    )
    return new_width, new_height


class UploadCommand(Command):
    """Add new image/video to the storage."""

    def __init__(
        self,
        dto: ParallelCommand,
        database: ParallelPostgreSQLDatabase,
        users: impl_sqlalchemy.UsersRepo,
        items: impl_sqlalchemy.ItemsRepo,
        meta: impl_sqlalchemy.MetaRepo,
        locator: FilesystemLocator,
        executor: ProcessPoolExecutor,
        object_storage: AbsObjectStorage,
    ) -> None:
        """Initialize instance."""
        super().__init__(dto)
        self.database = database
        self.users = users
        self.items = items
        self.meta = meta
        self.locator = locator
        self.executor = executor
        self.object_storage = object_storage

    async def execute(self) -> int:
        """Start execution of the command."""
        oid = self.dto.extras.get('oid')

        if oid is None:
            msg = 'oid is missing'
            raise KeyError(msg)

        if not isinstance(oid, int):
            msg = 'oid is invalid'
            raise TypeError(msg)

        item_id = self.dto.item_id

        async with self.database.transaction() as conn:
            item = await self.items.get_by_id(conn, item_id)
            owner = await self.users.get_by_id(conn, item.owner_id)

        content_type = self.dto.extras.get('content_type')
        if content_type is None:
            msg = 'content_type is missing'
            raise KeyError(msg)

        ext = self.dto.extras.get('ext')
        if ext is None:
            msg = 'ext is missing'
            raise KeyError(msg)

        if content_type in const.CONTENT_TYPE_IMAGES:
            segments = self.locator.get_path_segments(
                owner, item, const.MediaType.CONTENT, force_ext=ext
            )
            is_video = False
        else:
            segments = self.locator.get_path_segments(
                owner, item, const.MediaType.VIDEO, force_ext=ext
            )
            is_video = True

        if segments is None:
            msg = f'Failed to create content path for item {item.id}'
            raise ValueError(msg)

        skip_content = self.dto.extras.get('skip_content')
        extract_exif = self.dto.extras.get('extract_exif')
        _ = extract_exif
        # TODO - add exif processing
        # TODO - add signatures processing

        _root, _media, _uuid, _prefix, _filename = segments
        content_folder = _root / _media / _uuid / _prefix
        preview_folder = _root / const.MediaType.PREVIEW / _uuid / _prefix
        thumbnail_folder = _root / const.MediaType.THUMBNAIL / _uuid / _prefix
        content_path = content_folder / _filename

        await aiofiles.os.makedirs(content_folder, exist_ok=True)
        await aiofiles.os.makedirs(preview_folder, exist_ok=True)
        await aiofiles.os.makedirs(thumbnail_folder, exist_ok=True)
        content_existed = await aiofiles.os.path.exists(content_path)

        chunks = self.object_storage.read(oid)
        content_size = 0

        async with aiofiles.open(content_path, mode='wb') as f:
            async for chunk in chunks:
                await f.write(chunk)
                content_size += len(chunk)

        preview_path = self.locator.get_path(
            owner, item, const.MediaType.PREVIEW, force_ext='jpg'
        )
        if preview_path is None:
            msg = f'Failed to create preview path for item {item.id}'
            raise ValueError(msg)
        preview_existed = await aiofiles.os.path.exists(preview_path)

        thumbnail_path = self.locator.get_path(
            owner, item, const.MediaType.THUMBNAIL, force_ext='jpg'
        )
        if thumbnail_path is None:
            msg = f'Failed to create thumbnail path for item {item.id}'
            raise ValueError(msg)
        thumbnail_existed = await aiofiles.os.path.exists(thumbnail_path)

        loop = asyncio.get_running_loop()

        content_width, content_height = await loop.run_in_executor(
            self.executor,
            get_dimensions,
            content_path,
            is_video,
        )

        (
            preview_width,
            preview_height,
            preview_size,
        ) = await loop.run_in_executor(
            self.executor,
            save_image,
            content_path,
            preview_path,
            is_video,
            const.PREVIEW_SIZE,
        )

        (
            thumbnail_width,
            thumbnail_height,
            thumbnail_size,
        ) = await loop.run_in_executor(
            self.executor,
            save_image,
            content_path,
            thumbnail_path,
            is_video,
            const.THUMBNAIL_SIZE,
        )

        if skip_content:
            with suppress(FileNotFoundError):
                await aiofiles.os.unlink(content_path)

        for label, existed, path in [
            ('content', content_existed, content_path),
            ('preview', preview_existed, preview_path),
            ('thumbnail', thumbnail_existed, thumbnail_path),
        ]:
            if existed:
                LOG.warning('Overwrote {} file: {}', label, path)
            else:
                LOG.debug('Saved {} file: {}', label, path)

        total_size = content_size + preview_size + thumbnail_size

        async with self.database.transaction() as conn:
            metainfo = await self.meta.get_by_item(conn, item)

            metainfo.content_width = content_width
            metainfo.content_height = content_height
            metainfo.content_size = content_size

            metainfo.preview_width = preview_width
            metainfo.preview_height = preview_height
            metainfo.preview_size = preview_size

            metainfo.thumbnail_width = thumbnail_width
            metainfo.thumbnail_height = thumbnail_height
            metainfo.thumbnail_size = thumbnail_size

            metainfo.updated_at = pu.now()
            await self.meta.save(conn, metainfo)

            item.status = models.Status.AVAILABLE
            item.content_ext = ext
            item.preview_ext = 'jpg'
            item.thumbnail_ext = 'jpg'
            await self.items.save(conn, item)

        return total_size


def get_dimensions(src_path: Path, is_video: bool) -> tuple[int, int]:
    """Get image dimensions."""
    if is_video:
        clip = None
        try:
            clip = VideoFileClip(src_path)
            first_frame = clip.get_frame(0)
            img = Image.fromarray(first_frame)
            width, height = img.size
        finally:
            if clip is not None:
                clip.close()
    else:
        with Image.open(src_path) as img:
            width, height = img.size

    return width, height


def save_image(
    src_path: Path,
    dst_path: Path,
    is_video: bool,
    size: int,
) -> tuple[int, int, int]:
    """Create preview file."""
    if is_video:
        clip = None
        try:
            clip = VideoFileClip(src_path)
            first_frame = clip.get_frame(0)
            img = Image.fromarray(first_frame)
            width, height = resize(img, size, dst_path)
        finally:
            if clip is not None:
                clip.close()
    else:
        with Image.open(src_path) as img:
            width, height = resize(img, size, dst_path)

    return width, height, os.path.getsize(dst_path)
