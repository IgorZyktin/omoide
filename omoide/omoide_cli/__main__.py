"""Manual CLI operations."""

import typer

from omoide.omoide_cli.audit import main as audit_module
from omoide.omoide_cli.db import main as db
from omoide.omoide_cli.display import main as display
from omoide.omoide_cli.fs import main as filesystem
from omoide.omoide_cli.signatures import main as signatures

app = typer.Typer()

app.command()(audit_module.audit)

app.add_typer(db.app, name='db')
app.add_typer(display.app, name='display')
app.add_typer(filesystem.app, name='fs')
app.add_typer(signatures.app, name='signatures')

if __name__ == '__main__':
    app()
