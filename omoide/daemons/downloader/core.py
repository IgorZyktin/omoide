# -*- coding: utf-8 -*-
"""Downloader daemon.

Downloads processed images from database to the local storages(s).
We're using database as a medium.
"""
from omoide.daemons.common import action_class
from omoide.daemons.common import out
from omoide.daemons.downloader import cfg
from omoide.daemons.downloader import db


def download_items_from_database_to_storages(
        config: cfg.DownloaderConfig,
        database: db.Database,
        output: out.Output,
) -> list[action_class.Action]:
    """Do the actual download job."""
    # TODO - add logic here
    return []
