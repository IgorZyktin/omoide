"""Perform full recalculation of computed tags."""

from omoide import models
from omoide import utils as global_utils
from omoide.database.implementations import impl_sqlalchemy
from omoide.omoide_cli import utils


async def run():
    """Entry point."""
    db_url = utils.get_env('OMOIDE__DB_URL_ADMIN')
    database = impl_sqlalchemy.SqlalchemyDatabase(
        db_url=db_url,
        echo=False,
    )
    items_repo = impl_sqlalchemy.ItemsRepo()
    tags_repo = impl_sqlalchemy.TagsRepo()
    items_cache: dict[int, models.Item] = {}
    tags_cache: dict[int, set[str]] = {}

    try:
        async with database.transaction() as conn:
            root_items = await items_repo.select(conn, parent_id=None)

        for root_item in root_items:
            await rebuild_tags(database, items_repo, tags_repo, root_item, items_cache, tags_cache)
    finally:
        await database.disconnect()


async def rebuild_tags(
    database: impl_sqlalchemy.SqlalchemyDatabase,
    items_repo: impl_sqlalchemy.ItemsRepo,
    tags_repo: impl_sqlalchemy.TagsRepo,
    item: models.Item,
    items_cache: dict[int, models.Item],
    tags_cache: dict[int, set[str]],
) -> None:
    """Rebuild tags for specific item."""
    parent = items_cache.get(item.parent_id)
    parent_tags = tags_cache.get(item.parent_id, set())

    if parent is None:
        computed_tags = item.get_computed_tags(parent_name='', parent_tags=set())
    else:
        computed_tags = item.get_computed_tags(parent_name=parent.name, parent_tags=parent_tags)

    items_cache[item.id] = item
    tags_cache[item.id] = computed_tags

    async with database.transaction() as conn:
        label = item.name if item.name else item.uuid
        existing_computed_tags = await tags_repo.get_computed_tags(conn, item)
        if existing_computed_tags != computed_tags:
            delta = global_utils.get_delta(existing_computed_tags, computed_tags)
            print(f'Saving {label}, delta={sorted(delta)}')  # noqa: T201
            await tags_repo.save_computed_tags(conn, item, computed_tags)
        else:
            print(f'\033[K\rSkipping {label}', end='')  # noqa: T201

        children = await items_repo.get_children(conn, item)

    for child in children:
        await rebuild_tags(database, items_repo, tags_repo, child, items_cache, tags_cache)
