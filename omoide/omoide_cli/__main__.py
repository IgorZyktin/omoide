"""Manual CLI operations."""

import typer

from omoide.omoide_cli.display import main as display
from omoide.omoide_cli.signatures import main as signatures

app = typer.Typer()
app.add_typer(display.app, name='display')
app.add_typer(signatures.app, name='signatures')

if __name__ == '__main__':
    app()
