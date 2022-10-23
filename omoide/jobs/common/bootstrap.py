# -*- coding: utf-8 -*-
"""Operations that needs to be done before job start.
"""
import contextlib
from typing import Callable
from typing import Iterator

import sqlalchemy
from sqlalchemy.engine import Engine

from omoide.jobs.job_config import JobConfig

__all__ = [
    'apply_cli_kwargs_to_config',
    'temporary_engine',
    'Output',
]


def apply_cli_kwargs_to_config(config: JobConfig, **kwargs) -> None:
    """Apply CLI settings to the config instance."""
    for key, value in kwargs.items():
        setattr(config, key, value)


@contextlib.contextmanager
def temporary_engine(config: JobConfig) -> Iterator[Engine]:
    """Create engine and dispose it after completion."""
    engine = sqlalchemy.create_engine(
        config.db_url.get_secret_value(),
        echo=False,
    )

    try:
        yield engine
    finally:
        engine.dispose()


class Output:
    """Object that performs printing for jobs."""

    def __init__(self, silent: bool) -> None:
        """Initialize instance."""
        self.silent = silent

        if silent:
            self.print = self.print_dummy
        else:
            self.print = print  # type: ignore

    def print_dummy(self, *args, **kwargs) -> None:
        """Do nothing."""

    def print_config(self, config: JobConfig) -> None:
        """Human-readable display of the given config."""
        if self.silent:
            return

        self.print('Config:')

        for key, value in config.dict().items():
            self.print(f'\t{key}={value!r}')

    def table_line(
            self,
            *columns: int,
            sep: str = '-',
            corner: str = '+',
    ) -> None:
        """Print separation line for a table.

        Example:
            +------+------+---------+---------------------+--------+
        """
        if self.silent:
            return

        segments = [sep * x for x in columns]
        line = corner + corner.join(segments) + corner
        self.print(line)

    def table_row(
            self,
            *columns: str,
            row_formatter: Callable[..., list[str]],
            sep: str = '|',
    ) -> None:
        """Print row for the table.

        Example:
            | 01 |  test  | other         |
        """
        if self.silent:
            return

        segments = row_formatter(*columns)

        line = sep + sep.join(segments) + sep
        self.print(line)
