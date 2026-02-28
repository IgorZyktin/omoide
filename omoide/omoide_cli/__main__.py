"""Manual CLI operations."""

import json
from typing import Annotated

import sqlalchemy as sa
import typer

from omoide.omoide_cli import utils
from omoide.omoide_cli.audit import main as audit_module
from omoide.omoide_cli.db import main as db
from omoide.omoide_cli.display import main as display
from omoide.omoide_cli.fs import main as filesystem
from omoide.omoide_cli.signatures import code as signatures

app = typer.Typer(no_args_is_help=True)

app.command()(audit_module.audit)


@app.command()
def fix_signatures(
    check_missing: Annotated[
        bool,
        typer.Option(help='Find missing signatures'),
    ] = True,
    fix_missing: Annotated[
        bool,
        typer.Option(help='Automatically create missing signatures'),
    ] = False,
    check_mismatching: Annotated[
        bool,
        typer.Option(help='Find mismatching signatures'),
    ] = False,
    fix_mismatching: Annotated[
        bool,
        typer.Option(help='Automatically fix mismatching signatures'),
    ] = False,
    output: Annotated[
        str | None,
        typer.Option(help='Save results to a file'),
    ] = None,
    marker: Annotated[
        int,
        typer.Option(help='Id of last processed item'),
    ] = -1,
    limit: Annotated[
        int,
        typer.Option(help='Maximum amount of rows to process'),
    ] = 100,
) -> None:
    """Check that signatures correspond to files, fix if need to."""
    db_url = utils.get_env('OMOIDE_CLI__DB__URL')
    data_folder = utils.get_path('OMOIDE_CLI__DATA_FOLDER')
    site_url = utils.get_env('OMOIDE_CLI__SITE_URL')

    engine = sa.create_engine(db_url, pool_pre_ping=True, future=True)

    if check_missing:
        signatures.fix_missing_signatures(engine, data_folder, site_url, fix_missing, marker, limit)

    if check_mismatching:
        diff = signatures.fix_mismatching_signatures(
            engine, data_folder, site_url, fix_mismatching, marker, limit
        )

        if output and diff:
            with open(output, mode='w', encoding='utf-8') as file:
                json.dump(diff, file, ensure_ascii=False, indent=4)


app.add_typer(db.app, name='db')
app.add_typer(display.app, name='display')
app.add_typer(filesystem.app, name='fs')

if __name__ == '__main__':
    app()
