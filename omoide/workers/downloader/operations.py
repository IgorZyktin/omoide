"""Download operations."""

import hashlib
import zlib
from io import BytesIO
from pathlib import Path
from typing import Any

import python_utilz as pu
from PIL import ExifTags
from PIL import Image
from moviepy import VideoFileClip

from omoide import const
from omoide import models
from omoide.workers.downloader.cfg import WorkerDownloaderConfig
from omoide.workers.downloader.database import DownloaderPostgreSQLDatabase

IFD_CODE_LOOKUP = {i.value: i.name for i in ExifTags.IFD}


def download_media(
    config: WorkerDownloaderConfig,
    database: DownloaderPostgreSQLDatabase,
    model: models.OutputMedia,
) -> None:
    """Download to a file."""
    the_last_one = is_the_last_one(database)

    if model.ext:
        filename = f'{model.item_uuid}.{model.ext}'
    else:
        filename = str(model.item_uuid)

    folder = (
        config.data_folder
        / model.media_type
        / str(model.user_uuid)
        / str(model.item_uuid)[:config.prefix_size]
    )
    folder.mkdir(exist_ok=True)
    path = folder / filename

    if path.exists():
        moment = pu.now().isoformat().replace(':', '-').replace('T', '_')
        new_name = f'{filename}___replaced___{moment}'
        new_path = folder / new_name
        path.rename(new_path)

    item_id = database.get_item_id(model.item_uuid)

    if model.media_type == const.CONTENT:
        download_content(database, model, path, item_id, the_last_one=the_last_one)
    elif model.media_type == const.PREVIEW:
        download_preview(database, model, path, item_id, the_last_one=the_last_one)
    elif model.media_type == const.THUMBNAIL:
        download_thumbnail(database, model, path, item_id, the_last_one=the_last_one)
    elif model.media_type == const.VIDEO:
        download_video(database, model, path, item_id, the_last_one=the_last_one)
    else:
        msg = 'Unknown media type'
        raise NameError(msg)

    if the_last_one and database.fully_downloaded(item_id):
        database.mark_available(item_id)


def is_the_last_one(database: DownloaderPostgreSQLDatabase) -> bool:
    """Return true if we're the last worker in queue.

    Currently not used.
    """
    _ = database
    return True


def download_content(
    database: DownloaderPostgreSQLDatabase,
    model: models.OutputMedia,
    path: Path,
    item_id: int,
    *,
    the_last_one: bool,
) -> None:
    """Download to content."""
    path.write_bytes(model.content)

    stream = BytesIO(model.content)
    with Image.open(stream) as img:
        content_width, content_height = img.size

    if the_last_one:
        if model.extras.get('process_exif'):
            exif = process_exif(model)
            if exif.exif:
                database.save_exif(item_id, exif)

        signature_crc32 = zlib.crc32(model.content)
        database.save_cr32_signature(item_id, signature_crc32)

        signature_md5 = hashlib.md5(model.content).hexdigest()
        database.save_md5_signature(item_id, signature_md5)

        item_id = database.get_item_id(model.item_uuid)
        database.update_metainfo(
            item_id=item_id,
            updated_at=pu.now(),
            content_width=content_width,
            content_height=content_height,
            content_size=len(model.content),
        )


def download_preview(
    database: DownloaderPostgreSQLDatabase,
    model: models.OutputMedia,
    path: Path,
    item_id: int,
    *,
    the_last_one: bool,
) -> None:
    """Download to preview."""
    path.write_bytes(model.content)

    stream = BytesIO(model.content)
    with Image.open(stream) as img:
        preview_width, preview_height = img.size

    if the_last_one:
        database.update_metainfo(
            item_id=item_id,
            updated_at=pu.now(),
            preview_width=preview_width,
            preview_height=preview_height,
            preview_size=len(model.content),
        )


def download_thumbnail(
    database: DownloaderPostgreSQLDatabase,
    model: models.OutputMedia,
    path: Path,
    item_id: int,
    *,
    the_last_one: bool,
) -> None:
    """Download to thumbnails."""
    path.write_bytes(model.content)

    stream = BytesIO(model.content)
    with Image.open(stream) as img:
        thumbnail_width, thumbnail_height = img.size

    if the_last_one:
        database.update_metainfo(
            item_id=item_id,
            updated_at=pu.now(),
            thumbnail_width=thumbnail_width,
            thumbnail_height=thumbnail_height,
            thumbnail_size=len(model.content),
        )


def download_video(
    database: DownloaderPostgreSQLDatabase,
    model: models.OutputMedia,
    path: Path,
    item_id: int,
    *,
    the_last_one: bool,
) -> None:
    """Download to video."""
    path.write_bytes(model.content)

    if the_last_one:
        with VideoFileClip(path) as clip:
            subclip = clip.subclip(0, 5)  # first 5 seconds
            database.update_metainfo(
                item_id=item_id,
                updated_at=pu.now(),
                content_width=subclip.w,
                content_height=subclip.h,
                content_size=len(model.content),
            )


def process_exif(model: models.OutputMedia) -> models.Exif:
    """Extract exif data from content."""
    exif: dict[str, Any] = {}
    stream = BytesIO(model.content)

    def cast(maybe_string: Any) -> str:
        """Convert to string. Also strip unicode \u0000."""
        return str(maybe_string).replace('\u0000', '')

    with Image.open(stream) as img:
        img_exif = img.getexif()

        for tag_code, value in img_exif.items():
            if tag_code in IFD_CODE_LOOKUP:
                ifd_tag_name = cast(IFD_CODE_LOOKUP[tag_code])

                if ifd_tag_name not in exif:
                    exif[ifd_tag_name] = {}

                ifd_data = img_exif.get_ifd(tag_code).items()

                for nested_key, nested_value in ifd_data:
                    nested_tag_name = (
                        ExifTags.GPSTAGS.get(nested_key, None)
                        or ExifTags.TAGS.get(nested_key, None)
                        or nested_key
                    )
                    exif[ifd_tag_name][cast(nested_tag_name)] = cast(nested_value)

            else:
                exif[cast(ExifTags.TAGS.get(tag_code))] = cast(value)

    return models.Exif(exif=exif)
