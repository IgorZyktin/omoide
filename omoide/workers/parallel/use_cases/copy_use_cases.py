"""Use cases for parallel operations."""

from collections.abc import Callable
from functools import partial
from pathlib import Path
import shutil
from uuid import UUID

from omoide import const
from omoide import operations
from omoide.workers.parallel.use_cases.base_use_case import BaseParallelWorkerUseCase


def copy_media(  # noqa: PLR0913
    data_folder: Path,
    media_type: str,
    owner_uuid: str,
    source_item_uuid: str,
    target_item_uuid: str,
    source_item_ext: str,
    target_item_ext: str,
    prefix_size: int,
) -> None:
    """Copy single file."""
    source_name = f'{source_item_uuid}.{source_item_ext}'
    target_name = f'{target_item_uuid}.{target_item_ext}'
    source_path = (
        data_folder / media_type / owner_uuid / source_item_uuid[:prefix_size] / source_name
    )
    target_path = (
        data_folder / media_type / owner_uuid / target_item_uuid[:prefix_size] / target_name
    )

    shutil.copy2(source_path, target_path)


class CopyUseCase(BaseParallelWorkerUseCase):
    """Use case for copying media between items."""

    async def execute(self, operation: operations.Operation) -> Callable:
        """Perform workload."""
        async with self.mediator.database.transaction() as conn:
            source_item = await self.mediator.items.get_by_uuid(
                conn=conn,
                uuid=UUID(operation.extras['source_item_uuid']),
            )
            target_item = await self.mediator.items.get_by_uuid(
                conn=conn,
                uuid=UUID(operation.extras['target_item_uuid']),
            )
            owner_uuid = operation.extras['owner_uuid']

            if operation.extras['media_type'] == const.CONTENT:
                source_ext = source_item.content_ext or ''
            elif operation.extras['media_type'] == const.PREVIEW:
                source_ext = source_item.preview_ext or ''
            else:
                source_ext = source_item.thumbnail_ext or ''

            target_ext = source_ext

            return partial(
                copy_media,
                self.config.data_folder,
                operation.extras['media_type'],
                str(owner_uuid),
                str(source_item.uuid),
                str(target_item.uuid),
                source_ext,
                target_ext,
                self.config.prefix_size,
            )
