# -*- coding: utf-8 -*-
"""Job configuration.
"""
import os
import sys

from pydantic import BaseSettings, validator


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
    db_url: str  # regular database URI
    hot_folder: str  # path to storage with fast response
    cold_folder: str  # path to storage with regular response
    copy_all: bool  # flag that forces script to use hot storage as a cold one

    @validator('hot_folder', 'cold_folder')
    def ensure_folder_exists(cls, v):
        if not os.path.exists(v):
            sys.exit(f'Folder {v} does not exist')
        return v

    class Config:
        env_prefix = 'omoide_'
        env_nested_delimiter = '__'


class JobConfig(Config):
    """Additional CLI parameters for the job.

    Will be overwritten after start.
    """
    silent: bool = False  # print output during work or just do it silently
    batch_size: int = 50  # process no more than this amount of objects at once
    limit: int = -1  # process no more that this amount of objects
