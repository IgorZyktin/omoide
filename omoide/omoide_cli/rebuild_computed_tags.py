"""Perform full recalculation of computed tags."""

from omoide import models
from omoide import utils as global_utils
from omoide.database.implementations import impl_sqlalchemy
from omoide.omoide_cli import utils

ITEMS_REPO = impl_sqlalchemy.ItemsRepo()
TAGS_REPO = impl_sqlalchemy.TagsRepo()
TAGS_CACHE: dict[int, set[str]] = {}
PROCESSED_ITEMS = 0


async def run():
    """Entry point."""
    db_url = utils.get_env('OMOIDE__DB_URL_ADMIN')
    database = impl_sqlalchemy.SqlalchemyDatabase(
        db_url=db_url,
        echo=False,
    )

    try:
        async with database.transaction() as conn:
            root_items = await ITEMS_REPO.select(conn, parent_id=None)
            total_items = await ITEMS_REPO.count_all(conn)

        for root_item in root_items:
            await rebuild_tags(database, root_item, total_items)

    finally:
        await database.disconnect()


async def rebuild_tags(
    database: impl_sqlalchemy.SqlalchemyDatabase,
    item: models.Item,
    total_items: int,
) -> None:
    """Rebuild tags for specific item."""
    global PROCESSED_ITEMS  # noqa: PLW0603
    PROCESSED_ITEMS += 1
    percent = (PROCESSED_ITEMS / (total_items or 1)) * 100
    percent_str = f'{percent:.2f}'

    parent_tags = TAGS_CACHE.get(item.parent_id, set())
    computed_tags = item.get_computed_tags(parent_tags=parent_tags)
    TAGS_CACHE[item.id] = computed_tags

    async with database.transaction() as conn:
        label = item.name if item.name else item.uuid
        existing_computed_tags = await TAGS_REPO.get_computed_tags(conn, item)

        if existing_computed_tags != computed_tags:
            added, deleted = global_utils.get_delta(existing_computed_tags, computed_tags)
            print(  # noqa: T201
                f'[{percent_str}%] Saving {label}, added={sorted(added)}, deleted={sorted(deleted)}'
            )
            await TAGS_REPO.save_computed_tags(conn, item, computed_tags)
        else:
            print(f'\033[K\r[{percent_str}%] Skipping {label}', end='')  # noqa: T201

        children = await ITEMS_REPO.get_children(conn, item)

    for child in children:
        await rebuild_tags(database, child, total_items)
