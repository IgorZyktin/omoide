# -*- coding: utf-8 -*-
"""Refresh cache for known tags.
"""
from omoide import utils
from omoide.commands.application.refresh_known_tags import db
from omoide.commands.application.refresh_known_tags.cfg import Config
from omoide.commands.common.base_db import BaseDatabase
from omoide.infra import custom_logging

LOG = custom_logging.get_logger(__name__)


def run(
        config: Config,
        database: BaseDatabase,
) -> None:
    """Execute command."""
    if config.known:
        LOG.info('Refreshing tags for known users...')
        for user in db.get_users(database):
            total, count, to_drop = db \
                .refresh_known_tags_for_known_user(database, user)
            LOG.info(
                'Refreshed tags for user '
                '{} (got {} tags with {} occurrences)',
                user.name,
                utils.sep_digits(total),
                utils.sep_digits(count),
            )

            if to_drop:
                dropped = db.drop_known_tags_for_known_user(database,
                                                            user, to_drop)
                LOG.info('Dropped {} tags for user {}', dropped, user.name)

    if config.anon:
        LOG.info('Refreshing tags for anon user...')
        total, count, to_drop = db.refresh_known_tags_for_anon_user(database)
        LOG.info(
            'Refreshed tags for anon user (got {} tags with {} occurrences)',
            utils.sep_digits(total),
            utils.sep_digits(count),
        )

        if to_drop:
            dropped = db.drop_known_tags_for_anon_user(database, to_drop)
            LOG.info('Dropped {} tags for anon', dropped)
