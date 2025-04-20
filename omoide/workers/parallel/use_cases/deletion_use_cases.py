"""Use cases for parallel operations."""

from collections.abc import Callable
from functools import partial
from pathlib import Path

import python_utilz as pu

from omoide import custom_logging
from omoide import operations
from omoide.workers.parallel.use_cases.base_use_case import BaseParallelWorkerUseCase

LOG = custom_logging.get_logger(__name__)


def soft_delete_media(
    data_folder: Path,
    media_type: str,
    owner_uuid: str,
    item_uuid: str,
    ext: str,
    prefix_size: int,
) -> None:
    """Soft-delete single file."""
    old_name = f'{item_uuid}.{ext}'
    old_path = data_folder / media_type / owner_uuid / item_uuid[:prefix_size] / old_name
    moment = pu.now().isoformat().replace(':', '-').replace('T', '_')
    new_name = f'deleted___{moment}___{item_uuid}.{ext}'
    new_path = data_folder / media_type / owner_uuid / item_uuid[:prefix_size] / new_name

    if old_path.exists():
        old_path.rename(new_path)


class SoftDeleteMediaUseCase(BaseParallelWorkerUseCase):
    """Use case for soft deleting media."""

    async def execute(self, operation: operations.SoftDeleteMediaOp) -> Callable:
        """Perform workload."""
        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(
                conn=conn,
                uuid=operation.item_uuid,
                read_deleted=True,
            )
            owner = await self.mediator.users.get_by_id(conn, item.owner_id)

            return partial(
                soft_delete_media,
                self.config.data_folder,
                operation.media_type,
                str(owner.uuid),
                str(item.uuid),
                item.content_ext or '',
                self.config.prefix_size,
            )


def hard_delete_media(
    data_folder: Path,
    media_type: str,
    owner_uuid: str,
    item_uuid: str,
    ext: str,
    prefix_size: int,
) -> None:
    """Soft-delete single file."""
    old_name = f'{item_uuid}.{ext}'
    old_path = data_folder / media_type / owner_uuid / item_uuid[:prefix_size] / old_name
    old_path.unlink()


class HardDeleteMediaUseCase(BaseParallelWorkerUseCase):
    """Use case for hard deleting media."""

    async def execute(self, operation: operations.SoftDeleteMediaOp) -> Callable:
        """Perform workload."""
        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(conn, operation.item_uuid)
            owner = await self.mediator.users.get_by_id(conn, item.owner_id)

            return partial(
                hard_delete_media,
                self.config.data_folder,
                operation.media_type,
                str(owner.uuid),
                str(item.uuid),
                item.content_ext or '',
                self.config.prefix_size,
            )
