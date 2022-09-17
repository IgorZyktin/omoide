# -*- coding: utf-8 -*-
"""FS Operator setup as run-once cli command.
"""
from omoide import utils
from omoide.daemons.common import utils as daemon_utils
from omoide.daemons.downloader import cfg
from omoide.daemons.downloader import db
from omoide.daemons.downloader import misc
from omoide.daemons.fs_operator import fs_operations


@misc.cli_arguments
def main(**kwargs):
    """Entry point."""
    config = cfg.DownloaderConfig()
    daemon_utils.apply_cli_kwargs_to_config(config, **kwargs)
    output = misc.get_output_instance_for_fs_operator(config)
    database = db.Database(config=config)

    output.print('Started <FS Operator> as a command')
    output.print_config(config)
    output.print_line()
    output.print_header()
    output.print_line()

    with database.life_cycle():
        actions = fs_operations.perform_filesystem_operations(
            config=config,
            database=database,
            output=output,
        )

    done = sum(1 for x in actions if x.is_done())
    failed = sum(1 for x in actions if x.is_failed())

    if done or failed:
        output.print_line()

    if done:
        output.print(f'Performed {done} operations.')

    if failed:
        output.print(f'Failed to perform {failed} operations.')

    duration = (utils.now() - config.started_at).total_seconds()
    output.print(f'Took {duration:0.1f} sec.')


if __name__ == '__main__':
    main()
