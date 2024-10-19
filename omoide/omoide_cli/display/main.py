"""Operations that show output on screen."""

from uuid import UUID

import typer

from omoide import const
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
        env_variable=const.ENV_DB_URL_ADMIN,
    )
    code.inheritance(item_uuid, db_url, show_uuids)


@app.command()
def du(
    only_users: list[UUID] | None = None,
    db_url: str | None = None,
) -> None:
    """Show disk usage by users."""
    db_url = common.extract_env(
        what='Database URL',
        variable=db_url,
        env_variable=const.ENV_DB_URL_ADMIN,
    )
    code.du(only_users, db_url)


if __name__ == '__main__':
    app()
