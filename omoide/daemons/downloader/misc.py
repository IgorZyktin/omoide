# -*- coding: utf-8 -*-
"""Miscellaneous tools for downloader.
"""
from omoide.daemons.common import out
from omoide.daemons.downloader import cfg


def get_output_instance_for_downloader(
        config: cfg.DownloaderConfig,
) -> out.Output:
    """Perform basic setup for the output."""
    return out.Output(silent=config.silent)
