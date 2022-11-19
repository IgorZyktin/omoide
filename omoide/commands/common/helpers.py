# -*- coding: utf-8 -*-
"""Utils for commands.
"""
import contextlib
import time
from typing import Callable
from typing import Iterator
from uuid import UUID

import sqlalchemy
from sqlalchemy.engine import Engine


@contextlib.contextmanager
def temporary_engine(url: str) -> Iterator[Engine]:
    """Create engine and dispose it after completion."""
    engine = sqlalchemy.create_engine(
        url,
        echo=False,
    )

    try:
        yield engine
    finally:
        engine.dispose()


TPL = str | None | Callable[[], str | None]


@contextlib.contextmanager
def timing(
        callback: Callable = print,
        start_template: TPL = lambda: None,
        end_template: TPL = 'Finished in {delta:0.2f} seconds',
) -> Iterator[None]:
    """Create engine and dispose it after completion."""

    def _get_template(template: TPL) -> str | None:
        if template is None or not template:
            return None

        if isinstance(template, str):
            return template

        return template() or None

    def _maybe_print(template: str | None, **kwargs) -> None:
        if template:
            callback(template.format(**kwargs))

    full_start_template = _get_template(start_template)
    full_end_template = _get_template(end_template)

    started_at = time.perf_counter()
    try:
        _maybe_print(full_start_template)
        yield
    finally:
        ended_at = time.perf_counter()
        delta = ended_at - started_at
        _maybe_print(full_end_template, delta=delta)


def get_prefix(uuid: UUID, prefix_size: int) -> str:
    """Return prefix for given uuid."""
    return str(uuid)[0:prefix_size]
