"""Add new image/video to the storage."""

import asyncio
import math
import os
from concurrent.futures import ProcessPoolExecutor
from contextlib import suppress
from dataclasses import dataclass
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
from omoide.database import interfaces as db_interfaces
from omoide.infra.locators import FilesystemLocator
from omoide.models import ParallelCommand
from omoide.object_storage.interfaces import AbsObjectStorage
from omoide.workers.parallel.commands.base_command import Command
from omoide.workers.parallel.database import ParallelPostgreSQLDatabase

LOG = custom_logging.get_logger(__name__)


@dataclass(frozen=True)
class ConversionInput:
    """Description for conversion."""

    content_path: Path
    preview_path: Path
    thumbnail_path: Path
    is_video: bool
    preview_width: int
    thumbnail_width: int
    image_quality: int
    extract_exif: bool


@dataclass(frozen=True)
class ConversionOutput:
    """Conversion results."""

    content_width: int
    content_height: int
    content_size: int
    preview_width: int
    preview_height: int
    preview_size: int
    thumbnail_width: int
    thumbnail_height: int
    thumbnail_size: int


class UploadCommand(Command):
    """Add new image/video to the storage."""

    def __init__(
        self,
        dto: ParallelCommand,
        database: ParallelPostgreSQLDatabase,
        users: db_interfaces.AbsUsersRepo,
        items: db_interfaces.AbsItemsRepo,
        meta: db_interfaces.AbsMetaRepo,
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

    def get_required_resources(self) -> list[const.LockableResource]:
        """Return resources to lock before execution."""
        return [
            const.LockableResource(const.LockNamespace.ITEMS, self.dto.item_id)
        ]

    async def execute(self) -> int:
        """Start execution of the command."""
        if self.dto.oid is None:
            msg = 'oid is missing'
            raise KeyError(msg)

        async with self.database.transaction() as conn:
            item = await self.items.get_by_id(conn, self.dto.item_id)
            owner = await self.users.get_by_id(conn, item.owner_id)

        (
            content_path,
            preview_path,
            thumbnail_path,
            is_video,
            ext,
        ) = await self._get_paths_and_create_folders(owner, item)

        content_existed = await aiofiles.os.path.exists(content_path)
        preview_existed = await aiofiles.os.path.exists(preview_path)
        thumbnail_existed = await aiofiles.os.path.exists(thumbnail_path)

        chunks = self.object_storage.read(self.dto.oid)
        async with aiofiles.open(content_path, mode='wb') as f:
            async for chunk in chunks:
                await f.write(chunk)

        skip_content = bool(self.dto.extras.get('skip_content'))
        extract_exif = bool(self.dto.extras.get('extract_exif'))

        conversion_input = ConversionInput(
            content_path=content_path,
            preview_path=preview_path,
            thumbnail_path=thumbnail_path,
            is_video=is_video,
            preview_width=const.PREVIEW_SIZE,
            thumbnail_width=const.THUMBNAIL_SIZE,
            image_quality=const.IMAGE_QUALITY,
            extract_exif=extract_exif,
        )

        loop = asyncio.get_running_loop()
        conversion_output = await loop.run_in_executor(
            self.executor, perform_all_conversions, conversion_input
        )

        for label, existed, path in [
            (const.MediaType.CONTENT, content_existed, content_path),
            (const.MediaType.PREVIEW, preview_existed, preview_path),
            (const.MediaType.THUMBNAIL, thumbnail_existed, thumbnail_path),
        ]:
            if existed:
                LOG.warning('Overwrote {} file: {}', label, path)
            else:
                LOG.debug('Saved {} file: {}', label, path)

        if skip_content:
            with suppress(FileNotFoundError):
                await aiofiles.os.unlink(content_path)

        async with self.database.transaction() as conn:
            metainfo = await self.meta.get_by_item(conn, item)

            if skip_content:
                metainfo.content_width = None
                metainfo.content_height = None
                metainfo.content_size = None
                item.content_ext = None
            else:
                metainfo.content_width = conversion_output.content_width
                metainfo.content_height = conversion_output.content_height
                metainfo.content_size = conversion_output.content_size
                item.content_ext = ext

            item.preview_ext = 'jpg'
            item.thumbnail_ext = 'jpg'

            item.status = models.Status.AVAILABLE
            await self.items.save(conn, item)

            metainfo.preview_width = conversion_output.preview_width
            metainfo.preview_height = conversion_output.preview_height
            metainfo.preview_size = conversion_output.preview_size

            metainfo.thumbnail_width = conversion_output.thumbnail_width
            metainfo.thumbnail_height = conversion_output.thumbnail_height
            metainfo.thumbnail_size = conversion_output.thumbnail_size

            metainfo.updated_at = pu.now()
            await self.meta.save(conn, metainfo)

        return (
            conversion_output.content_size
            + conversion_output.preview_size
            + conversion_output.thumbnail_size
        )

    async def _get_paths_and_create_folders(
        self,
        owner: models.User,
        item: models.Item,
    ) -> tuple[Path, Path, Path, bool, str]:
        """Create data folders and return resulting paths."""
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
            msg = f'Failed to create content/video path for item {item.id}'
            raise ValueError(msg)

        _root, _media, _uuid, _prefix, _filename = segments
        content_folder = _root / _media / _uuid / _prefix
        preview_folder = _root / const.MediaType.PREVIEW / _uuid / _prefix
        thumbnail_folder = _root / const.MediaType.THUMBNAIL / _uuid / _prefix
        content_path = content_folder / _filename

        await aiofiles.os.makedirs(content_folder, exist_ok=True)
        await aiofiles.os.makedirs(preview_folder, exist_ok=True)
        await aiofiles.os.makedirs(thumbnail_folder, exist_ok=True)

        preview_path = self.locator.get_path(
            owner, item, const.MediaType.PREVIEW, force_ext='jpg'
        )
        if preview_path is None:
            msg = f'Failed to create preview path for item {item.id}'
            raise ValueError(msg)

        thumbnail_path = self.locator.get_path(
            owner, item, const.MediaType.THUMBNAIL, force_ext='jpg'
        )
        if thumbnail_path is None:
            msg = f'Failed to create thumbnail path for item {item.id}'
            raise ValueError(msg)

        return content_path, preview_path, thumbnail_path, is_video, ext


def perform_all_conversions(
    conversion_input: ConversionInput,
) -> ConversionOutput:
    """Create all sub-images, calculate signatures."""
    if conversion_input.is_video:
        clip = None
        img = None
        try:
            clip = VideoFileClip(conversion_input.content_path)
            first_frame = clip.get_frame(0)
            img = Image.fromarray(first_frame)
            (
                preview_width,
                preview_height,
                thumbnail_width,
                thumbnail_height,
            ) = do_resizes(img, conversion_input)
            content_width, content_height = img.size
        finally:
            if clip is not None:
                clip.close()
            if img is not None:
                img.close()
    else:
        with Image.open(conversion_input.content_path) as img:
            content_width, content_height = img.size
            (
                preview_width,
                preview_height,
                thumbnail_width,
                thumbnail_height,
            ) = do_resizes(img, conversion_input)

    return ConversionOutput(
        content_width=content_width,
        content_height=content_height,
        content_size=os.path.getsize(conversion_input.content_path),
        preview_width=preview_width,
        preview_height=preview_height,
        preview_size=os.path.getsize(conversion_input.preview_path),
        thumbnail_width=thumbnail_width,
        thumbnail_height=thumbnail_height,
        thumbnail_size=os.path.getsize(conversion_input.thumbnail_path),
    )


def do_resizes(
    img: Image.Image,
    conversion_input: ConversionInput,
) -> tuple[int, int, int, int]:
    """Resize source image."""
    preview_width, preview_height = resize(
        img,
        conversion_input.preview_width,
        conversion_input.preview_path,
        conversion_input.image_quality,
    )
    thumbnail_width, thumbnail_height = resize(
        img,
        conversion_input.thumbnail_width,
        conversion_input.thumbnail_path,
        conversion_input.image_quality,
    )
    return (
        preview_width,
        preview_height,
        thumbnail_width,
        thumbnail_height,
    )


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


def resize(img: Image.Image, size: int, dst_path: Path, quality: int) -> tuple[int, int]:
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
        quality=quality,
        optimize=True,
    )
    return new_width, new_height
