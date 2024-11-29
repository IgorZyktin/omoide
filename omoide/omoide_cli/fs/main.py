"""Operations related to filesystem."""

import asyncio
from pathlib import Path
import sys
from uuid import UUID

import typer

from omoide import const
from omoide import custom_logging
from omoide import utils
from omoide.omoide_cli import common
from omoide.omoide_cli.fs import code_hard_delete
from omoide.omoide_cli.fs import code_organize
from omoide.omoide_cli.fs import code_refresh
from omoide.omoide_cli.fs import code_sync

app = typer.Typer()

LOG = custom_logging.get_logger(__name__)


@app.command()
def refresh_file_sizes(  # noqa: PLR0913 Too many arguments in function definition
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

    coro = code_refresh.refresh_file_sizes(
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
def refresh_image_dimensions(  # noqa: PLR0913 Too many arguments in function definition
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

    coro = code_refresh.refresh_image_dimensions(
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


@app.command()
def sync(
    main_folder: Path,
    replica_folder: Path,
    only_users: list[UUID] | None = None,
    verbose: bool = True,
    dry_run: bool = True,
    limit: int = -1,
) -> None:
    """Synchronize files in different content folders."""
    if not main_folder.exists():
        LOG.error('Main folder does not exist: {}', main_folder.absolute())
        sys.exit(1)

    if not replica_folder.exists():
        LOG.error('Replica folder does not exist: {}', replica_folder.absolute())
        sys.exit(1)

    coro = code_sync.sync(
        main_folder=main_folder,
        replica_folder=replica_folder,
        only_users=only_users,
        verbose=verbose,
        dry_run=dry_run,
        limit=limit,
    )
    total = asyncio.run(coro)

    if dry_run:
        LOG.warning('Will perform {total} operations during sync', total=total)
    else:
        LOG.info('Performed {total} operations during sync', total=total)


@app.command()
def hard_delete(
    folder: str,
    only_users: list[UUID] | None = None,
    dry_run: bool = True,
    limit: int = -1,
) -> None:
    """Delete files that looks soft-deleted."""
    valid_folder = common.extract_folder(folder)

    coro = code_hard_delete.hard_delete(
        folder=valid_folder,
        only_users=only_users,
        dry_run=dry_run,
        limit=limit,
    )

    LOG.info('Performing hard delete for files in {}', folder)
    total_files, total_bytes = asyncio.run(coro)

    if dry_run:
        LOG.info(
            'Will delete {total_files} files and free {total_size} of space',
            total_files=utils.sep_digits(total_files),
            total_size=utils.human_readable_size(total_bytes),
        )
    else:
        LOG.info(
            'Deleted {total_files} files and free {total_size} of space',
            total_files=utils.sep_digits(total_files),
            total_size=utils.human_readable_size(total_bytes),
        )


@app.command()
def organize(
    source: Path,
    archive: Path,
    db_url: str | None = None,
    inject_year: bool = True,
    dry_run: bool = False,
    limit: int = -1,
) -> None:
    """Move files from source folder to archive folder according to item structure."""
    valid_db_url = common.extract_env(
        what='Database URL',
        variable=db_url,
        env_variable=const.ENV_DB_URL_ADMIN,
    )

    if not source.exists():
        msg = f'Source folder does not exist: {source}'
        raise RuntimeError(msg)

    if not archive.exists():
        msg = f'Archive folder does not exist: {archive}'
        raise RuntimeError(msg)

    LOG.info('Organizing image files according to item structure')
    LOG.info(' Source folder: {}', source)
    LOG.info('Archive folder: {}', archive)

    total_files, total_bytes = code_organize.organize(
        source=source,
        archive=archive,
        db_url=valid_db_url,
        inject_year=inject_year,
        dry_run=dry_run,
        limit=limit,
    )

    if dry_run:
        LOG.info(
            'Will move {total_files} files ({total_size})',
            total_files=utils.sep_digits(total_files),
            total_size=utils.human_readable_size(total_bytes),
        )
    else:
        LOG.info(
            'Moved {total_files} files ({total_size})',
            total_files=utils.sep_digits(total_files),
            total_size=utils.human_readable_size(total_bytes),
        )


if __name__ == '__main__':
    app()
