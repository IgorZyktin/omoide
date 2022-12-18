# -*- coding: utf-8 -*-
"""Refresh cache for known tags.
"""
import time

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
    if config.known or config.only_user:
        LOG.info('Refreshing tags for known users...')
        if config.only_user:
            users = [db.get_user(database, config.only_user)]
        else:
            users = [db.get_users(database)]

        for user in users:
            start = time.perf_counter()
            total, count, to_drop = db \
                .refresh_known_tags_for_known_user(database, user)
            spent = time.perf_counter() - start
            LOG.info(
                'Refreshed tags for '
                '{} (got {} tags with {} occurrences) in {:0.3f} sec.',
                user.name,
                utils.sep_digits(total),
                utils.sep_digits(count),
                spent,
            )

            if to_drop:
                dropped = db.drop_known_tags_for_known_user(database,
                                                            user, to_drop)
                LOG.info('Dropped {} tags for {}', dropped, user.name)

    if config.anon:
        LOG.info('Refreshing tags for anon user...')
        start = time.perf_counter()
        total, count, to_drop = db.refresh_known_tags_for_anon_user(database)
        spent = time.perf_counter() - start
        LOG.info(
            'Refreshed tags for anon user '
            '(got {} tags with {} occurrences) in {:0.3f} sec.',
            utils.sep_digits(total),
            utils.sep_digits(count),
            spent
        )

        if to_drop:
            dropped = db.drop_known_tags_for_anon_user(database, to_drop)
            LOG.info('Dropped {} tags for anon', dropped)
