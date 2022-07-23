# -*- coding: utf-8 -*-
"""Downloader daemon.

Downloads processed images from database to the local storages(s).
We're using database as a medium.
"""
from omoide import utils
from omoide.daemons.common import action_class
from omoide.daemons.common import out
from omoide.daemons.downloader import cfg
from omoide.daemons.downloader import db
from omoide.storage.database import models


def download_items_from_database_to_storages(
        config: cfg.DownloaderConfig,
        database: db.Database,
        output: out.Output,
) -> list[action_class.Action]:
    """Do the actual download job."""
    actions = []
    with database.start_session():
        batch = database.get_media_to_download()

        for media in batch:
            action = action_class.Action(status='work')

            try:
                size = len(media.content)
                process_single_media(config, media)
                action.done()
            except Exception as exc:
                action.fail()

                if config.strict:
                    raise

                # TODO: replace it with proper logger call
                print(f'{type(exc).__name__}: {exc}')

            action.ended_at = utils.now()
            actions.append(action)

            if not config.dry_run:
                database.finalize_media(media, action.status)

            location = database.get_cached_location_for_an_item(
                item_uuid=media.item_uuid,
            )

            output.print_row(
                processed_at=str(action.ended_at.replace(microsecond=0)),
                uuid=str(media.item_uuid),
                type=str(media.media_type),
                size=utils.byte_count_to_text(size),
                status=action.status,
                location=utils.no_longer_than(location, 93),
            )

    return actions


def process_single_media(
        config: cfg.DownloaderConfig,
        media: models.Media,
) -> None:
    """Save one object."""
    # TODO
