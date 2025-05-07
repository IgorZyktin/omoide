"""Use cases for item introduction."""

from datetime import datetime
import hashlib
from io import BytesIO
import math
from typing import Any
from uuid import UUID
import zlib

from PIL import ExifTags
from PIL import Image
from PIL import ImageFilter
import python_utilz as pu

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide import operations
from omoide.workers.serial.use_cases.base_use_case import BaseSerialWorkerUseCase

IFD_CODE_LOOKUP = {i.value: i.name for i in ExifTags.IFD}
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
                exif = await self.process_exif(operation)
                if exif:
                    await self.mediator.exif.create(conn, item, exif)

            if last_modified := operation.extras['features']['last_modified']:
                metainfo.user_time = datetime.fromisoformat(last_modified).replace(tzinfo=None)

            metainfo.updated_at = pu.now()
            await self.mediator.meta.save(conn, metainfo)
            await self.mediator.meta.add_item_note(
                conn,
                item=item,
                key='original_filename',
                value=operation.extras['filename'],
            )

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
            new_img = new_img.convert('RGB')

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
            new_img = new_img.convert('RGB')

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

    @staticmethod
    async def process_exif(operation: operations.Operation) -> dict[str, str]:
        """Extract exif data from content."""
        exif: dict[str, Any] = {}
        stream = BytesIO(operation.payload)
        with Image.open(stream) as img:
            img_exif = img.getexif()

            for tag_code, value in img_exif.items():
                if tag_code in IFD_CODE_LOOKUP:
                    ifd_tag_name = str(IFD_CODE_LOOKUP[tag_code])

                    if ifd_tag_name not in exif:
                        exif[ifd_tag_name] = {}

                    ifd_data = img_exif.get_ifd(tag_code).items()

                    for nested_key, nested_value in ifd_data:
                        nested_tag_name = (
                            ExifTags.GPSTAGS.get(nested_key, None)
                            or ExifTags.TAGS.get(nested_key, None)
                            or nested_key
                        )
                        exif[ifd_tag_name][str(nested_tag_name)] = str(nested_value)

                else:
                    exif[str(ExifTags.TAGS.get(tag_code))] = str(value)

        return exif
