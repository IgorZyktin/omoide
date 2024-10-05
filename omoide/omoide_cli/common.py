"""Common code for all commands."""

import os
import sys

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
