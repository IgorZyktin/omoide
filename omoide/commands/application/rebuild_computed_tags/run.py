# -*- coding: utf-8 -*-
"""Refresh tags.
"""
import time

from omoide import utils
from omoide.commands.application.rebuild_computed_tags import db
from omoide.commands.application.rebuild_computed_tags.cfg import Config
from omoide.commands.common import helpers
from omoide.commands.common.base_db import BaseDatabase
from omoide.infra import custom_logging

LOG = custom_logging.get_logger(__name__)


def run(
        config: Config,
        database: BaseDatabase,
) -> None:
    """Execute command."""
    with database.start_session() as session:
        users = helpers.get_all_corresponding_users(session, config.only_users)

    for user in users:
        LOG.info('Refreshing tags for {} {}', user.uuid, user.name)
        start = time.perf_counter()

        with database.start_session() as session:
            children = db.refresh_tags(config, session, user)
            spent = time.perf_counter() - start
            LOG.info(
                'Refreshed tags for '
                '{} (with {} children) in {:0.3f} sec.',
                user.name,
                utils.sep_digits(children),
                spent,
            )
