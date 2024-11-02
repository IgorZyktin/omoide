"""Common code for all commands."""

import os
import sys
from pathlib import Path

from omoide import const
from omoide import custom_logging

LOG = custom_logging.get_logger(__name__)


def extract_env(what: str, variable: str | None, env_variable: str) -> str:
    """Get value or fail."""
    if variable is None:
        variable = os.getenv(env_variable)

        if variable is None:
            LOG.error(
                '{} is not given. '
                'Pass it directly to the command '
                'or set via {!r} environment variable',
                what,
                env_variable,
            )
            sys.exit(1)

    return variable


def extract_folder(folder: str | None) -> Path:
    """Return path to the content folder."""
    folder = extract_env(
        what='File storage path',
        variable=folder,
        env_variable=const.ENV_FOLDER,
    )

    folder_path = Path(folder)

    if not folder_path.exists():
        LOG.error('Storage folder does not exist: {!r}', folder)
        sys.exit(1)

    return folder_path
