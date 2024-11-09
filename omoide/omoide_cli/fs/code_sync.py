"""Implementation for sync filesystem command."""

from pathlib import Path

from omoide import custom_logging

LOG = custom_logging.get_logger(__name__)


async def sync(
    main_folder: Path,
    replica_folder: Path,
    verbose: bool,
    dry_run: bool,
) -> int:
    """Synchronize files in different content folders."""
    # TODO
    _ = main_folder
    _ = replica_folder
    _ = verbose
    _ = dry_run
    return 0
