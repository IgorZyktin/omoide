"""Code for initing a child process."""

import logging
import sys


def init_child() -> None:
    """Set up default logger."""
    logging.basicConfig(
        level=logging.WARNING,
        format='[child %(process)d] %(levelname)s %(name)s: %(message)s',
        stream=sys.stderr,
    )
