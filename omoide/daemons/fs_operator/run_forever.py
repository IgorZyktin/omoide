# -*- coding: utf-8 -*-
"""Downloader setup as a daemon.
"""
import time

from omoide.daemons.common import utils as daemon_utils
from omoide.daemons.downloader import cfg
from omoide.daemons.downloader import db
from omoide.daemons.fs_operator import fs_operations
from omoide.daemons.fs_operator import misc


@misc.cli_arguments
def main(**kwargs):
    """Entry point."""
    config = cfg.DownloaderConfig()
    daemon_utils.apply_cli_kwargs_to_config(config, **kwargs)
    output = misc.get_output_instance_for_fs_operator(config)
    database = db.Database(config=config)

    output.print('Started <FS Operator> as a daemon')
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

            fs_operations.perform_filesystem_operations(
                config=config,
                database=database,
                output=output,
            )


if __name__ == '__main__':
    main()
