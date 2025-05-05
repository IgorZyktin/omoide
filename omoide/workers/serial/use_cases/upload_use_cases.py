"""Use cases for item introduction."""

import hashlib
from io import BytesIO
import math
from typing import Any
from uuid import UUID
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
        new_width = float(min(old_width, new_size))
        coefficient = new_width / old_width
        new_height = old_height * coefficient
    else:
        new_height = min(old_height, new_size)
        coefficient = new_height / old_height
        new_width = old_width * coefficient

    return math.ceil(new_width), math.ceil(new_height)


class UploadItemUseCase(BaseSerialWorkerUseCase):
    """Use case for introducing an item."""

    async def execute(self, operation: operations.Operation) -> None:
        """Perform workload."""
        item_uuid = UUID(operation.extras['item_uuid'])

        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, item_uuid)
            owner = await self.mediator.users.get_by_id(conn, item.owner_id)
            metainfo = await self.mediator.meta.get_by_item(conn, item)

            await self.process_content(conn, owner, item, metainfo, operation)
            await self.process_preview(conn, owner, item, metainfo, operation)
            await self.process_thumbnail(conn, owner, item, metainfo, operation)

            if operation.extras['features']['extract_exif']:
                exif = await self.process_exif(item, operation)
                if exif:
                    await self.mediator.exif.create(conn, item, exif)

            metainfo.updated_at = pu.now()
            await self.mediator.meta.save(conn, metainfo)

            signature_crc32 = zlib.crc32(operation.payload)
            await self.mediator.signatures.save_cr32_signature(conn, item, signature_crc32)

            signature_md5 = hashlib.md5(operation.payload).hexdigest()
            await self.mediator.signatures.save_md5_signature(conn, item, signature_md5)

            await self.mediator.items.save(conn, item)

    async def process_content(
        self,
        conn: Any,
        owner: models.User,
        item: models.Item,
        metainfo: models.Metainfo,
        operation: operations.Operation,
    ) -> None:
        """Process and save content."""
        item.content_ext = operation.extras['ext']

        stream = BytesIO(operation.payload)
        with Image.open(stream) as img:
            metainfo.content_width, metainfo.content_height = img.size
            metainfo.content_size = len(operation.payload)
            metainfo.content_type = operation.extras['content_type']

        await self.mediator.misc.create_parallel_operation(
            conn=conn,
            name='download',
            extras={
                'requested_by': operation.extras['requested_by'],
                'owner_uuid': str(owner.uuid),
                'item_uuid': str(item.uuid),
                'media_type': const.CONTENT,
            },
            payload=operation.payload,
        )

    async def process_preview(
        self,
        conn: Any,
        owner: models.User,
        item: models.Item,
        metainfo: models.Metainfo,
        operation: operations.Operation,
    ) -> None:
        """Process and save preview."""
        item.preview_ext = 'jpg'
        stream = BytesIO(operation.payload)

        with Image.open(stream) as img:
            old_width, old_height = img.size
            new_width, new_height = get_new_image_dimensions(
                old_width, old_height, const.PREVIEW_SIZE
            )
            new_img = img.resize((new_width, new_height))
            new_img = new_img.filter(ImageFilter.SHARPEN)

            metainfo.preview_width, metainfo.preview_height = new_width, new_height

            buffer = BytesIO()
            new_img.save(buffer, 'JPEG', quality=const.IMAGE_QUALITY, optimize=True)
            new_payload = buffer.getvalue()

            metainfo.preview_size = len(new_payload)

        await self.mediator.misc.create_parallel_operation(
            conn=conn,
            name='download',
            extras={
                'requested_by': operation.extras['requested_by'],
                'owner_uuid': str(owner.uuid),
                'item_uuid': str(item.uuid),
                'media_type': const.PREVIEW,
            },
            payload=new_payload,
        )

    async def process_thumbnail(
        self,
        conn: Any,
        owner: models.User,
        item: models.Item,
        metainfo: models.Metainfo,
        operation: operations.Operation,
    ) -> None:
        """Process and save thumbnail."""
        item.thumbnail_ext = 'jpg'
        stream = BytesIO(operation.payload)

        with Image.open(stream) as img:
            old_width, old_height = img.size
            new_width, new_height = get_new_image_dimensions(
                old_width, old_height, const.THUMBNAIL_SIZE
            )
            new_img = img.resize((new_width, new_height))
            new_img = new_img.filter(ImageFilter.SHARPEN)

            metainfo.thumbnail_width, metainfo.thumbnail_height = new_width, new_height

            buffer = BytesIO()
            new_img.save(buffer, 'JPEG', quality=const.IMAGE_QUALITY, optimize=True)
            new_payload = buffer.getvalue()

            metainfo.thumbnail_size = len(new_payload)

        await self.mediator.misc.create_parallel_operation(
            conn=conn,
            name='download',
            extras={
                'requested_by': operation.extras['requested_by'],
                'owner_uuid': str(owner.uuid),
                'item_uuid': str(item.uuid),
                'media_type': const.THUMBNAIL,
            },
            payload=new_payload,
        )

    async def process_exif(
        self,
        item: models.Item,
        operation: operations.Operation,
    ) -> dict[str, str]:
        """Extract exif data from content."""
        del item
        del operation
        # TODO
        return {}
