"""Use cases for parallel operations."""

from collections.abc import Callable
from functools import partial
from pathlib import Path
from uuid import UUID

import python_utilz as pu

from omoide import custom_logging
from omoide import operations
from omoide.workers.parallel.use_cases.base_use_case import BaseParallelWorkerUseCase

LOG = custom_logging.get_logger(__name__)


def download_media(  # noqa: PLR0913
    data_folder: Path,
    media_type: str,
    owner_uuid: str,
    item_uuid: str,
    ext: str,
    prefix_size: int,
    payload: bytes,
) -> None:
    """Soft-delete single file."""
    if not payload:
        return

    name = f'{item_uuid}.{ext}'
    folder = data_folder / media_type / owner_uuid / item_uuid[:prefix_size]
    folder.mkdir(exist_ok=True)
    path = folder / name

    if path.exists():
        moment = pu.now().isoformat().replace(':', '-').replace('T', '_')
        new_name = f'replaced___{moment}___{item_uuid}.{ext}'
        new_path = folder / new_name
        path.rename(new_path)

    path.write_bytes(payload)


class DownloadUseCase(BaseParallelWorkerUseCase):
    """Use case for media downloading."""

    async def execute(self, operation: operations.ParallelOperation) -> Callable:
        """Perform workload."""
        async with self.mediator.database.transaction() as conn:
            item = await self.mediator.items.get_by_uuid(
                conn=conn,
                uuid=UUID(operation.extras['item_uuid']),
                read_deleted=True,
            )
            owner = await self.mediator.users.get_by_id(conn, item.owner_id)

            return partial(
                download_media,
                self.config.data_folder,
                operation.extras['media_type'],
                str(owner.uuid),
                str(item.uuid),
                item.content_ext or '',
                self.config.prefix_size,
                operation.payload,
            )
