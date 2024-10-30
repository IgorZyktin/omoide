"""Operations related to database contents."""

import asyncio
from uuid import UUID

import typer

from omoide import const
from omoide import custom_logging
from omoide.omoide_cli import common
from omoide.omoide_cli.db import code

app = typer.Typer()

LOG = custom_logging.get_logger(__name__)


@app.command()
def copy_images_from_children(
    db_url: str | None = None,
    verbose: bool = True,
    only_users: list[UUID] | None = None,
    only_items: list[UUID] | None = None,
    limit: int | None = None,
) -> None:
    """Force items to copy images from their children.

    May require you to run it more than one time.
    """
    db_url = common.extract_env(
        what='Database URL',
        variable=db_url,
        env_variable=const.ENV_DB_URL_ADMIN,
    )

    coro = code.copy_images_from_children(
        db_url=db_url,
        verbose=verbose,
        only_users=only_users,
        only_items=only_items,
        limit=limit,
    )
    total = asyncio.run(coro)

    LOG.info('Forced {total} items to copy image from their children', total=total)


if __name__ == '__main__':
    app()
