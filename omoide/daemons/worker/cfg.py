# -*- coding: utf-8 -*-
"""Worker configuration.
"""
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic import SecretStr
from pydantic import root_validator
from pydantic import validator

_LOG_LEVEL = Literal['DEBUG', 'INFO', 'WARNING', 'CRITICAL', 'ERROR', 'NOTSET']


class Config(BaseModel):
    """Worker configuration."""
    name: str
    db_url: SecretStr
    hot_folder: str
    cold_folder: str
    save_hot: bool
    save_cold: bool
    download_media: bool
    manual_copy: bool
    drop_done_media: bool
    drop_done_copies: bool
    min_interval: float
    max_interval: float
    warm_up_coefficient: float
    batch_size: int
    log_level: _LOG_LEVEL
    debug: bool
    prefix_size: int
    single_run: bool
    echo: bool
    replication_formula: dict[str, bool]

    class Config:
        allow_mutation = False

    @validator('min_interval')
    def check_min_interval(cls, v):
        if v <= 0.0:
            raise ValueError('Minimum interval is too small')

        if v >= 3600.0:
            raise ValueError('Minimum interval is too large')

        return v

    @validator('max_interval')
    def check_max_interval(cls, v, values):
        min_interval = values.get('min_interval', 0.0)

        if v <= min_interval:
            raise ValueError('Maximum interval is too small')

        if v >= 8760.0:
            raise ValueError('Maximum interval is too large')

        return v

    @validator('warm_up_coefficient')
    def check_warm_up_coefficient(cls, v):
        if v <= 1.0:
            raise ValueError('Warm up coefficient is too small')

        if v >= 1000.0:
            raise ValueError('Minimum interval is too large')

        return v

    @root_validator
    def check_at_least_one_folder_given(cls, values):
        hot_folder = values.get('hot_folder')
        cold_folder = values.get('cold_folder')

        if not any((hot_folder, cold_folder)):
            raise ValueError(
                'At least one of hot-folder/cold-folder folders must be given'
            )

        return values

    @root_validator
    def check_folders_are_adequate(cls, values):
        save_hot = values.get('save_hot')
        save_cold = values.get('save_cold')
        hot_folder = values.get('hot_folder')
        cold_folder = values.get('cold_folder')

        if save_hot and not hot_folder:
            raise ValueError(
                'You have to specify location of the hot folder to save there'
            )

        if save_cold and not cold_folder:
            raise ValueError(
                'You have to specify location of the cold folder to save there'
            )

        return values

    @root_validator
    def check_folders_exist(cls, values):
        save_hot = values.get('save_hot')
        save_cold = values.get('save_cold')
        hot_folder = values.get('hot_folder')
        cold_folder = values.get('cold_folder')

        hot_does_not_exist = not Path(hot_folder).exists()
        cold_does_not_exist = not Path(cold_folder).exists()

        if hot_does_not_exist and cold_does_not_exist:
            raise ValueError(
                'Both hot and cold folders do not exist: '
                f'hot_folder={hot_folder}, cold_folder={cold_folder!r}'
            )

        if save_hot and hot_does_not_exist:
            raise ValueError(f'Hot folder does not exist: {hot_folder!r}')

        if save_cold and cold_does_not_exist:
            raise ValueError(f'Cold folder does not exist: {cold_folder!r}')

        return values

    @validator('batch_size')
    def check_batch_size(cls, v):
        if v <= 0:
            raise ValueError('Batch size is too small')

        if v >= 100_000:
            raise ValueError('Batch size is too big')

        return v

    def verbose(self) -> str:
        """Convert config to human-readable string."""
        return '\n\t'.join((
            f'{key}={value}'
            for key, value in
            self.dict().items()
        ))
