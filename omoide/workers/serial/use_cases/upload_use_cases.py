"""Use cases for item introduction."""

import hashlib
import math
import zlib

from PIL import Image
from PIL import ImageFilter
import python_utilz as pu

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide import operations
from omoide.workers.serial.use_cases.base_use_case import BaseSerialWorkerUseCase

LOG = custom_logging.get_logger(__name__)


def get_new_image_dimensions(
    old_width: int,
    old_height: int,
    new_size: int,
) -> tuple[int, int]:
    """Calculate new size while maintaining proportions."""
    if old_width >= old_height:
        new_width = min(old_width, new_size)
        coefficient = new_width / old_width
        new_height = old_height * coefficient
    else:
        new_height = min(old_height, new_size)
        coefficient = new_height / old_height
        new_width = old_width * coefficient

    return math.ceil(new_width), math.ceil(new_height)


class UploadItemUseCase(BaseSerialWorkerUseCase):
    """Use case for introducing an item."""

    async def execute(self, operation: operations.UploadItemOp) -> None:
        """Perform workload."""
        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, operation.item_uuid)
            metainfo = await self.mediator.meta.get_by_item(conn, item)

            self.process_content(item, metainfo, operation)
            self.process_preview(item, metainfo)
            self.process_thumbnail(item, metainfo)

            if operation.file.features.extract_exif:
                exif = self.process_exif(item, operation)
                if exif:
                    await self.mediator.exif.create(conn, item, exif)

            # TODO - set file creation time

            metainfo.updated_at = pu.now()
            await self.mediator.meta.save(conn, metainfo)

            signature_crc32 = zlib.crc32(operation.payload)
            await self.mediator.signatures.save_cr32_signature(conn, item, signature_crc32)

            signature_md5 = hashlib.md5(operation.payload).hexdigest()
            await self.mediator.signatures.save_md5_signature(conn, item, signature_md5)

            item.status = models.Status.AVAILABLE
            await self.mediator.items.save(conn, item)

    def process_content(
        self,
        item: models.Item,
        metainfo: models.Metainfo,
        operation: operations.UploadItemOp,
    ) -> None:
        """Process and save content."""
        item.content_ext = operation.file.ext

        self.mediator.object_storage.save_content(item, operation.payload)
        path = self.mediator.object_storage.get_content_path(item)

        if path:
            LOG.info('Saving content: {}', path)
            with Image.open(path) as img:
                metainfo.content_width, metainfo.content_height = img.size
                metainfo.content_size = len(operation.payload)
                metainfo.content_type = operation.file.content_type

    def process_preview(
        self,
        item: models.Item,
        metainfo: models.Metainfo,
    ) -> None:
        """Process and save preview."""
        item.preview_ext = 'jpg'
        content_path = self.mediator.object_storage.get_content_path(item)
        preview_path = self.mediator.object_storage.get_preview_path(item)

        if content_path and preview_path:
            LOG.info('Saving preview: {}', content_path)
            with Image.open(content_path) as img:
                old_width, old_height = img.size
                new_width, new_height = get_new_image_dimensions(
                    old_width, old_height, const.PREVIEW_SIZE
                )
                new_img = img.resize((new_width, new_height))
                new_img = new_img.filter(ImageFilter.SHARPEN)
                preview_path.parent.mkdir(parents=True, exist_ok=True)
                new_img.save(preview_path)

                metainfo.preview_width, metainfo.preview_height = new_width, new_height
                new_payload = new_img.tobytes()
                metainfo.preview_size = len(new_payload)

    def process_thumbnail(
        self,
        item: models.Item,
        metainfo: models.Metainfo,
    ) -> None:
        """Process and save thumbnail."""
        item.thumbnail_ext = 'jpg'
        content_path = self.mediator.object_storage.get_content_path(item)
        thumbnail_path = self.mediator.object_storage.get_thumbnail_path(item)

        if content_path:
            LOG.info('Saving thumbnail: {}', content_path)
            with Image.open(content_path) as img:
                old_width, old_height = img.size
                new_width, new_height = get_new_image_dimensions(
                    old_width, old_height, const.THUMBNAIL_SIZE
                )
                new_img = img.resize((new_width, new_height))
                new_img = new_img.filter(ImageFilter.SHARPEN)
                thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
                new_img.save(thumbnail_path)

                metainfo.thumbnail_width, metainfo.thumbnail_height = new_width, new_height
                new_payload = new_img.tobytes()
                metainfo.thumbnail_size = len(new_payload)

    def process_exif(
        self,
        item: models.Item,
        operation: operations.UploadItemOp,
    ) -> dict[str, str]:
        """Extract exif data from content."""
        del item
        del operation
        # TODO
        return {}
