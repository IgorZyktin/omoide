"""Operations related to filesystem."""

import asyncio
from uuid import UUID

import typer

from omoide import const
from omoide import custom_logging
from omoide.omoide_cli import common
from omoide.omoide_cli.fs import code

app = typer.Typer()

LOG = custom_logging.get_logger(__name__)


@app.command()
def refresh_file_sizes(
    db_url: str | None = None,
    folder: str | None = None,
    verbose: bool = True,
    only_users: list[UUID] | None = None,
    only_items: list[UUID] | None = None,
    marker: int | None = None,
    batch_size: int = 100,
    limit: int | None = None,
) -> None:
    """Get actual file size for every image and save them into DB."""
    valid_db_url = common.extract_env(
        what='Database URL',
        variable=db_url,
        env_variable=const.ENV_DB_URL_ADMIN,
    )

    valid_folder = common.extract_folder(folder)

    coro = code.refresh_file_sizes(
        db_url=valid_db_url,
        folder=valid_folder,
        verbose=verbose,
        only_users=only_users,
        only_items=only_items,
        marker=marker,
        batch_size=batch_size,
        limit=limit,
    )
    total = asyncio.run(coro)

    LOG.info('Updated file sizes for {total} items', total=total)


@app.command()
def refresh_image_dimensions(
    db_url: str | None = None,
    folder: str | None = None,
    verbose: bool = True,
    only_users: list[UUID] | None = None,
    only_items: list[UUID] | None = None,
    marker: int | None = None,
    batch_size: int = 100,
    limit: int | None = None,
) -> None:
    """Get actual image dimensions for every image and save them into DB."""
    valid_db_url = common.extract_env(
        what='Database URL',
        variable=db_url,
        env_variable=const.ENV_DB_URL_ADMIN,
    )

    valid_folder = common.extract_folder(folder)

    coro = code.refresh_image_dimensions(
        db_url=valid_db_url,
        folder=valid_folder,
        verbose=verbose,
        only_users=only_users,
        only_items=only_items,
        marker=marker,
        batch_size=batch_size,
        limit=limit,
    )
    total = asyncio.run(coro)

    LOG.info('Updated image dimensions for {total} items', total=total)


if __name__ == '__main__':
    app()
