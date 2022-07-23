# -*- coding: utf-8 -*-
"""Downloader setup as run-once cli command.
"""
from omoide import utils
from omoide.daemons.common import utils as daemon_utils
from omoide.daemons.downloader import core, cfg, db, misc


@misc.cli_arguments
def main(**kwargs):
    """Entry point."""
    config = cfg.DownloaderConfig()
    daemon_utils.apply_cli_kwargs_to_config(config, **kwargs)
    output = misc.get_output_instance_for_downloader(config)
    database = db.Database(config=config)

    output.print('Started <DOWNLOADER> as a command')
    output.print_config(config)
    output.print_line()
    output.print_header()
    output.print_line()

    with database.life_cycle():
        actions = core.download_items_from_database_to_storages(
            config=config,
            database=database,
            output=output,
        )

    downloaded = sum(1 for x in actions if x.is_done())
    failed = sum(1 for x in actions if x.is_failed())

    if downloaded or failed:
        output.print_line()

    if downloaded:
        output.print(f'Downloaded {downloaded} media items.')

    if failed:
        output.print(f'Failed to download {failed} media items.')

    duration = (utils.now() - config.started_at).total_seconds()
    output.print(f'Took {duration:0.1f} sec.')


if __name__ == '__main__':
    main()
