"""Implementation that deletes soft deleted files."""

import os
from pathlib import Path
from uuid import UUID

from omoide import const
from omoide import custom_logging
from omoide import limits
from omoide import utils

LOG = custom_logging.get_logger(__name__)


async def hard_delete(
    folder: Path,
    only_users: list[UUID] | None,
    dry_run: bool,
    limit: int,
) -> int:
    """Delete all files that look soft-deleted."""
    total = 0
    sequence = [const.CONTENT, const.PREVIEW, const.THUMBNAIL]
    for target in sequence:
        LOG.info('Hard deleting files in {}', target)

        for user in (folder / target).iterdir():
            if not utils.is_valid_uuid(user.name):
                continue

            uuid = UUID(user.name)

            if only_users is not None and uuid not in only_users:
                continue

            for prefix in user.iterdir():
                total += process_prefix(prefix, dry_run, limit)

    return total


def process_prefix(prefix: Path, dry_run: bool, limit: int) -> int:
    """Process single item prefix."""
    total = 0
    for file in prefix.iterdir():
        if look_like_soft_deleted(file.stem, file.suffix):
            total += 1
            if dry_run:
                LOG.warning('Will delete {}', file)
            else:
                LOG.warning('Deleting {}', file)
                os.remove(file)

            if total >= limit != -1:
                return total

    return total


def look_like_soft_deleted(filename: str, suffix: str) -> bool:
    """Return True if file looks like soft-deleted."""
    if utils.is_valid_uuid(filename):
        return False

    if suffix.casefold().lstrip('.') not in limits.SUPPORTED_EXTENSION:
        return False

    # TODO - change template to a more strict one
    # TODO - add filtering for removal date
    return '___' in filename
