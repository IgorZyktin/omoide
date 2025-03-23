"""Implementation that deletes soft deleted files."""

import os
from pathlib import Path
from uuid import UUID

import python_utilz as pu

from omoide import const
from omoide import custom_logging
from omoide import limits

LOG = custom_logging.get_logger(__name__)


async def hard_delete(
    folder: Path,
    only_users: list[UUID] | None,
    dry_run: bool,
    limit: int,
) -> tuple[int, int]:
    """Delete all files that look soft-deleted."""
    total_files = 0
    total_bytes = 0

    sequence = [const.CONTENT, const.PREVIEW, const.THUMBNAIL]
    for target in sequence:
        LOG.info('Hard deleting files in {}', target)

        for user in (folder / target).iterdir():
            if not pu.is_valid_uuid(user.name):
                continue

            uuid = UUID(user.name)

            if only_users is not None and uuid not in only_users:
                continue

            for prefix in user.iterdir():
                local_files, local_bytes = process_prefix(prefix, dry_run, limit)
                total_files += local_files
                total_bytes += local_bytes

                if total_files >= limit != -1:
                    return total_files, total_bytes

    return total_files, total_bytes


def process_prefix(prefix: Path, dry_run: bool, limit: int) -> tuple[int, int]:
    """Process single item prefix."""
    total_files = 0
    total_bytes = 0

    for file in prefix.iterdir():
        if look_like_soft_deleted(file.stem, file.suffix):
            total_files += 1
            total_bytes += file.stat().st_size

            if dry_run:
                LOG.info('Will delete {}', file)
            else:
                LOG.warning('Deleting {}', file)
                os.remove(file)

            if total_files >= limit != -1:
                return total_files, total_bytes

    return total_files, total_bytes


def look_like_soft_deleted(filename: str, suffix: str) -> bool:
    """Return True if file looks like soft-deleted."""
    if pu.is_valid_uuid(filename):
        return False

    if suffix.casefold().lstrip('.') not in limits.SUPPORTED_EXTENSION:
        return False

    # TODO - change template to a more strict one
    # TODO - add filtering for removal date
    return '___' in filename
