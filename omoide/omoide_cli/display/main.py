"""Operations that show output on screen."""

from uuid import UUID

import typer

from omoide import custom_logging
from omoide.omoide_cli import common
from omoide.omoide_cli.display import code

app = typer.Typer()

LOG = custom_logging.get_logger(__name__)


@app.command()
def inheritance(
    item_uuid: UUID,
    db_url: str | None = None,
    show_uuids: bool = True,
) -> None:
    """Show children for given item."""
    db_url = common.extract_env(
        what='Database URL',
        variable=db_url,
        env_variable='OMOIDE__DB_URL_ADMIN',
    )
    code.inheritance(db_url, item_uuid, show_uuids)


if __name__ == '__main__':
    app()