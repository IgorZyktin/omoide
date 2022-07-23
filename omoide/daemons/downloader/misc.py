# -*- coding: utf-8 -*-
"""Miscellaneous tools for downloader.
"""
from omoide.daemons.common import out
from omoide.daemons.downloader import cfg


def get_output_instance_for_downloader(
        config: cfg.DownloaderConfig,
) -> out.Output:
    """Perform basic setup for the output."""
    output = out.Output(silent=config.silent)

    output.add_columns(
        out.Column(name='Processed at', width=27),
        out.Column(name='UUID', width=38),
        out.Column(name='Type', width=11),
        out.Column(name='Size', width=14),
        out.Column(name='Status', width=8),
        out.Column(name='Location', width=95),
    )

    return output
