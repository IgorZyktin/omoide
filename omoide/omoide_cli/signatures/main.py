"""Operations related to file signatures."""

import typer

from omoide import custom_logging
from omoide.omoide_cli.signatures import code

app = typer.Typer()

LOG = custom_logging.get_logger(__name__)


@app.command()
def update_md5(
    everything: bool = False,
    folder: str | None = None,
    db_url: str | None = None,
    batch_size: int = 100,
    limit: int | None = None,
) -> None:
    """Recalculate MD5 hashes."""
    folder_path, db_url = code.init(
        what='MD5',
        everything=everything,
        folder=folder,
        db_url=db_url,
    )

    total = code.process_items(
        what='MD5',
        db_url=db_url,
        batch_size=batch_size,
        folder_path=folder_path,
        limit=limit,
        everything=everything,
        executable=code.update_md5_for_item,
    )

    LOG.info('Finished updating MD5 hashes, affected items: {}', total)


@app.command()
def update_crc32(
    everything: bool = False,
    folder: str | None = None,
    db_url: str | None = None,
    batch_size: int = 100,
    limit: int | None = None,
) -> None:
    """Recalculate CRC32 hashes."""
    folder_path, db_url = code.init(
        what='CRC32',
        everything=everything,
        folder=folder,
        db_url=db_url,
    )

    total = code.process_items(
        what='CRC32',
        db_url=db_url,
        batch_size=batch_size,
        folder_path=folder_path,
        limit=limit,
        everything=everything,
        executable=code.update_crc32_for_item,
    )

    LOG.info('Finished updating CRC32 hashes, affected items: {}', total)


if __name__ == '__main__':
    app()
