# -*- coding: utf-8 -*-
"""Downloader setup as a daemon.
"""
import time

from omoide.daemons.common import utils as daemon_utils
from omoide.daemons.downloader import core, cfg, db, misc


@misc.cli_arguments
def main(**kwargs):
    """Entry point."""
    config = cfg.DownloaderConfig()
    daemon_utils.apply_cli_kwargs_to_config(config, **kwargs)
    output = misc.get_output_instance_for_downloader(config)
    database = db.Database(config=config)

    output.print('Started <DOWNLOADER> as a daemon')
    output.print_config(config)
    output.print_line()
    output.print_header()
    output.print_line()

    next_invocation = time.monotonic()

    with database.life_cycle():
        while True:
            delta = max(next_invocation - time.monotonic(), 0)
            next_invocation = time.monotonic() + config.download_interval
            time.sleep(delta)

            core.download_items_from_database_to_storages(
                config=config,
                database=database,
                output=output,
            )


if __name__ == '__main__':
    main()
