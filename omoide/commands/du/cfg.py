# -*- coding: utf-8 -*-
"""Command configuration.
"""
import os
import sys
from typing import Any

from pydantic import BaseSettings
from pydantic import SecretStr
from pydantic import validator


class Config(BaseSettings):
    """Command configuration."""
    db_url: SecretStr  # Regular database URI
    cold_folder: str  # Path to storage with regular response

    @classmethod
    @validator('cold_folder')
    def ensure_folder_exists(cls, value: Any):
        if not os.path.exists(value):
            sys.exit(f'Folder {value} does not exist')
        return value

    class Config:
        env_prefix = 'omoide_'
        env_nested_delimiter = '__'


def get_config() -> Config:
    """Get instance of the config."""
    return Config()
