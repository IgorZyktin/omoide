# -*- coding: utf-8 -*-
"""Downloader implementation.
"""
import os
import random
from pathlib import Path

from omoide import utils
from omoide.storage.database.models import Media
from omoide.jobs.downloader import filesystem


def download_single_entry(media: Media, paths: list[Path]) -> None:
    """Perform full download for single entry."""
    for path in paths:
        bucket = utils.get_bucket(media.item_uuid)
        filename = filesystem.create_folders_for_filename(
            path,
            str(media.item.owner_uuid),
            media.type,
            bucket,
            f'{media.item_uuid}.{media.ext}'
        )

        temp_filename = filename + '.tmp' + str(random.randint(1, 1000))

        filesystem.drop_if_exists(filename)
        filesystem.drop_if_exists(temp_filename)

        with open(temp_filename, 'wb') as file:
            file.write(media.content)
            file.flush()
            os.fsync(file.fileno())

        os.rename(temp_filename, filename)
