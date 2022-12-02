# -*- coding: utf-8 -*-
"""Command configuration.
"""
from typing import Optional
from uuid import UUID

from pydantic import BaseSettings
from pydantic import SecretStr


class Config(BaseSettings):
    """Command configuration."""
    db_url: SecretStr
    hot_folder: str
    cold_folder: str
    limit: int = -1
    prefix_size: int = 2
    marker: Optional[UUID] = None

    class Config:
        env_prefix = 'omoide_'
        env_nested_delimiter = '__'


def get_config() -> Config:
    """Get instance of the config."""
    return Config()
