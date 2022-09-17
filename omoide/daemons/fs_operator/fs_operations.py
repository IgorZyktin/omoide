# -*- coding: utf-8 -*-
"""Filesystem operations.
"""
import json
import os

from omoide import utils
from omoide.daemons.common import action_class
from omoide.daemons.common import out
from omoide.daemons.downloader import cfg
from omoide.daemons.downloader import db
from omoide.storage.database import models


def perform_filesystem_operations(
        config: cfg.DownloaderConfig,
        database: db.Database,
        output: out.Output,
) -> list[action_class.Action]:
    """Do the actual download job."""
    actions = []
    with database.start_session():
        batch = database.get_fs_operations_to_perform()

        for command in batch:
            action = action_class.Action(status='work')

            error = ''
            try:
                if process_single_command(config, database, command):
                    action.done()
                else:
                    action.fail()
            except Exception as exc:
                action.fail()

                if config.strict:
                    raise

                # TODO: replace it with proper logger call
                print(f'{type(exc).__name__}: {exc}')

            action.ended_at = utils.now()
            actions.append(action)

            if not config.dry_run:
                database.finalize_fs_operation(command, action.status, error)

            location = database.get_cached_location_for_an_item(
                item_uuid=command.target_uuid,
            )

            output.print_row(
                processed_at=str(action.ended_at.replace(microsecond=0,
                                                         tzinfo=None)),
                from_uuid=str(command.source_uuid),
                to_uuid=str(command.target_uuid),
                operation=command.operation,
                status=action.status,
                location=utils.no_longer_than(' ' + location, 93),
            )

    return actions


def process_single_command(
        config: cfg.DownloaderConfig,
        database: db.Database,
        command: models.FilesystemOperation,
) -> bool:
    """Save one object. Return True on success."""
    if command.operation == 'copy-thumbnail':
        return process_copy_thumbnail(config, database, command)

    raise RuntimeError(f'Unknown operation: {command.operation}')


def process_copy_thumbnail(
        config: cfg.DownloaderConfig,
        database: db.Database,
        command: models.FilesystemOperation,
) -> bool:
    """Copy thumbnail from source to target."""
    if config.dry_run:
        return True

    extras = json.loads(command.extras)

    bucket = utils.get_bucket(command.source_uuid)
    filename = os.path.join(
        config.hot_folder,
        'thumbnail',
        extras['owner_uuid'],
        bucket,
        f'{command.source_uuid}.{extras["ext"]}',
    )

    with open(filename, mode='rb') as file:
        content = file.read()

    if not content:
        return False

    database.create_new_media(command, content, extras['ext'])

    return True
