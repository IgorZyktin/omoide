"""Common code for all commands."""

import os
import sys
from pathlib import Path
from uuid import UUID

from omoide import const
from omoide import custom_logging
from omoide.database.implementations.impl_sqlalchemy import ItemsRepo
from omoide.database.implementations.impl_sqlalchemy import MetaRepo
from omoide.database.implementations.impl_sqlalchemy import SqlalchemyDatabase
from omoide.database.implementations.impl_sqlalchemy import UsersRepo
from omoide.object_storage.implementations.file_client import FileObjectStorageClient

LOG = custom_logging.get_logger(__name__)


def extract_env(what: str, variable: str | None, env_variable: str) -> str:
    """Get value or fail."""
    if variable is None:
        variable = os.getenv(env_variable)

        if variable is None:
            LOG.error(
                '{} is not given. '
                'Pass it directly to the command '
                'or set via {!r} environment variable',
                what,
                env_variable,
            )
            sys.exit(1)

    return variable


def extract_folder(folder: str | None) -> Path:
    """Return path to the content folder."""
    folder = extract_env(
        what='File storage path',
        variable=folder,
        env_variable=const.ENV_FOLDER,
    )

    folder_path = Path(folder)

    if not folder_path.exists():
        LOG.error('Storage folder does not exist: {!r}', folder)
        sys.exit(1)

    return folder_path


def loop_condition(total: int, limit: int | None, total_in_batch: int, batch_size: int) -> bool:
    """Cycle stop condition."""
    if limit is not None and total == limit:
        return False

    return not (total_in_batch != 0 and total_in_batch < batch_size)


async def init_variables(
    db_url: str,
    only_users: list[UUID] | None,
    only_items: list[UUID] | None,
) -> tuple[
    SqlalchemyDatabase,
    UsersRepo,
    ItemsRepo,
    MetaRepo,
    set[int],
    set[int],
]:
    """Create all needed variables to start the loop."""
    users = UsersRepo()
    items = ItemsRepo()
    meta = MetaRepo()

    database = SqlalchemyDatabase(db_url)

    async with database.transaction() as conn:
        only_user_ids = await users.cast_uuids(conn, only_users or set())
        only_item_ids = await items.cast_uuids(conn, only_items or set())

    return database, users, items, meta, only_user_ids, only_item_ids
