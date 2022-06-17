# -*- coding: utf-8 -*-
"""Operations that needs to be done before job start.
"""
import contextlib

import sqlalchemy
from sqlalchemy.engine import Engine

from omoide.jobs.job_config import JobConfig

__all__ = [
    'apply_cli_kwargs_to_config',
    'temporary_engine',
]


def apply_cli_kwargs_to_config(config: JobConfig, **kwargs) -> None:
    """Apply CLI settings to the config instance."""
    for key, value in kwargs.items():
        setattr(config, key, value)


@contextlib.contextmanager
def temporary_engine(config: JobConfig) -> Engine:
    """Create engine and dispose it after completion."""
    engine = sqlalchemy.create_engine(config.db_url, echo=False)

    try:
        yield engine
    finally:
        engine.dispose()
