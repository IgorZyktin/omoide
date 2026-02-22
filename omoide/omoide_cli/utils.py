"""Common CLI utils."""

import os
from pathlib import Path
import sys

from omoide import custom_logging

LOG = custom_logging.get_logger(__name__)


def get_env(name: str) -> str:
    """Get environment variable."""
    variable = os.getenv(name)

    if variable is None:
        LOG.error(
            'You have to set environment variable: {}',
            name,
        )
        sys.exit(1)

    return variable


def get_path(name: str) -> Path:
    """Get path from environment variable."""
    path = Path(get_env(name))

    if not path.exists():
        LOG.error('Folder does not exist: {}', name)
        sys.exit(1)

    return path
