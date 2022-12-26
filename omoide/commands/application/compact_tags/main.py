# -*- coding: utf-8 -*-
"""Comapct tags.
"""
import time

from omoide import utils
from omoide.commands.application.compact_tags import db
from omoide.commands.application.compact_tags.cfg import Config
from omoide.commands.common import helpers
from omoide.commands.common.base_db import BaseDatabase
from omoide.infra import custom_logging

LOG = custom_logging.get_logger(__name__)


def run(
        config: Config,
        database: BaseDatabase,
) -> None:
    """Execute command."""
    if config.only_user:
        users = []
        user = helpers.get_user(database, config.only_user)
        if user:
            users.append(user)
    else:
        LOG.info('Compacting tags for all users...')
        users = helpers.get_users(database)

    for user in users:
        LOG.info('Compacting tags for {} {}', user.uuid, user.name)
        start = time.perf_counter()

        with database.start_session() as session:
            children = db.compact_tags(config, session, user)
            spent = time.perf_counter() - start
            LOG.info(
                'Compacted tags for '
                '{} (with {} children) in {:0.3f} sec.',
                user.name,
                utils.sep_digits(children),
                spent,
            )
