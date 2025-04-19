"""Worker that performs operations one by one."""

import asyncio

import nano_settings as ns
import typer

from omoide import custom_logging
from omoide.database.implementations import impl_sqlalchemy as sa
from omoide.workers.common import runtime
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial.cfg import SerialWorkerConfig
from omoide.workers.serial.worker import SerialWorker

app = typer.Typer()


@app.command()
def main() -> None:
    """Entry point."""
    asyncio.run(_main())


async def _main() -> None:
    """Async entry point."""
    config = ns.from_env(SerialWorkerConfig, env_prefix='omoide_serial_worker')

    custom_logging.init_logging(
        level=config.log_level,
        diagnose=config.log_diagnose,
        path=config.log_path,
        rotation=config.log_rotation,
    )

    mediator = WorkerMediator(
        database=sa.SqlalchemyDatabase(config.db_url.get_secret_value()),
        items=sa.ItemsRepo(),
        tags=sa.TagsRepo(),
        users=sa.UsersRepo(),
        workers=sa.WorkersRepo(),
        misc=sa.MiscRepo(),
    )

    worker = SerialWorker(config, mediator, name=config.name)

    await runtime.run_automatic(
        worker=worker,
        short_delay=config.short_delay,
        long_delay=config.long_delay,
    )


if __name__ == '__main__':
    app()
