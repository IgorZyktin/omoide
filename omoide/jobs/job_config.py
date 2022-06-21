# -*- coding: utf-8 -*-
"""Job configuration.
"""
import os
import sys
from typing import Any

from pydantic import BaseSettings, validator, SecretStr


class Config(BaseSettings):
    """Job configuration.

    Logic behind storage settings:
        Storages are divided into hot and cold. Hot one is supposed to be
        represented as a fast SSD drive located as close to the server as
        possible. Cold one is supposed to be bigger and slower HDD storage,
        possibly external to the server and connected via network. This design
        supposes that hot storage will be used only for thumbnails and cold one
        will store everything (including additional copy of thumbnails).
        As long as hot storage is big enough, 'copy_all' variable makes it
        possible to treat hot storage same way as cold and store there
        everything (full copy).
    """
    db_url: SecretStr  # Regular database URI
    hot_folder: str  # Path to storage with fast response
    cold_folder: str  # Path to storage with regular response
    copy_all: bool  # Flag that forces script to use hot storage as a cold one

    @classmethod
    @validator('hot_folder', 'cold_folder')
    def ensure_folder_exists(cls, value: Any):
        if not os.path.exists(value):
            sys.exit(f'Folder {value} does not exist')
        return value

    class Config:
        env_prefix = 'omoide_'
        env_nested_delimiter = '__'


class JobConfig(Config):
    """Additional CLI parameters for the job.

    Will be overwritten after start.
    """
    silent: bool = False  # Print output during work or just do it silently
    dry_run: bool = True  # Run script, but do not save changes
    strict: bool = True  # Stop processing on first error or complete all
    batch_size: int = 50  # Process this amount of objects at once
    limit: int = -1  # Maximum amount of items to process (-1 for infinity)
    max_attempts: int = 3  # Stop trying to process object after X fails
