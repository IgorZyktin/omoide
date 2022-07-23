# -*- coding: utf-8 -*-
"""Downloader setup as run-once cli command.
"""
from omoide import utils
from omoide.daemons.common import utils as daemon_utils
from omoide.daemons.downloader import core, cfg, db, misc


@core.cli_arguments
def main(**kwargs):
    """Entry point."""
    config = cfg.DownloaderConfig()
    daemon_utils.apply_cli_kwargs_to_config(config, **kwargs)
    output = misc.get_output_instance_for_downloader(config)
    database = db.Database(config=config)

    output.print('Started <DOWNLOADER> as a command')
    output.print_config(config)
    output.print_header()

    with database.life_cycle():
        actions = core.download_items_from_database_to_storages(
            config=config,
            database=database,
            output=output,
        )

    output.print_line()

    message = 'Downloaded {} media items.'.format(
        sum(x for x in actions if x.is_done())
    )
    failed = sum(x for x in actions if x.is_failed())
    if failed:
        message += f'\nFailed to download {failed} media items.'

    duration = (utils.now() - config.started_at).total_seconds()
    message += f'\nTook {duration:0.1f} sec.'

    output.print(message)


if __name__ == '__main__':
    main()
