"""Worker settings.
"""
from functools import cache
from pathlib import Path
from typing import Any
from typing import Literal
from typing import TypeAlias

import pydantic
import pydantic_settings


class Media(pydantic.BaseModel):
    """Desired way of media processing."""
    should_process: bool = True
    drop_after: bool = True
    replication_formula: dict[str, bool] = pydantic.Field(default_factory=dict)


class Copy(pydantic.BaseModel):
    """Desired way of copy processing."""
    should_process: bool = True
    drop_after: bool = True


MINIMAL_DELAY = 0.001
SECONDS_IN_HOUR = 3600.0
SECONDS_IN_DAY = 8760.0


class TimerStrategy(pydantic.BaseModel):
    """Settings for timer handling (if active)."""
    min_interval: float = 0.1
    max_interval: float = 300.0
    warm_up_coefficient: float = 1.3

    @pydantic.model_validator(mode='after')
    def check_min_interval(self) -> 'TimerStrategy':
        """Check."""
        if self.min_interval <= MINIMAL_DELAY:
            msg = f'Minimum interval is too small (limit is {MINIMAL_DELAY})'
            raise ValueError(msg)

        if self.min_interval >= SECONDS_IN_HOUR:
            msg = f'Minimum interval is too large (limit is {SECONDS_IN_HOUR})'
            raise ValueError(msg)

        return self

    @pydantic.model_validator(mode='after')
    def check_max_interval(self) -> 'TimerStrategy':
        """Check."""
        if self.max_interval <= self.min_interval:
            msg = ('Max interval must be bigger '
                   f'than min interval (limit is {self.min_interval})')
            raise ValueError(msg)

        if self.max_interval >= SECONDS_IN_DAY:
            msg = f'Maximum interval is too large (limit is {SECONDS_IN_DAY})'
            raise ValueError(msg)

        return self

    @pydantic.model_validator(mode='after')
    def check_warm_up_coefficient(self) -> 'TimerStrategy':
        """Check."""
        if self.warm_up_coefficient <= 1.0:
            msg = 'Warm up coefficient is too small (limit is 1.0)'
            raise ValueError(msg)

        if self.warm_up_coefficient >= 100.0:
            msg = 'Warm up coefficient is too big (limit is 100.0)'
            raise ValueError(msg)

        return self


LOG_LEVEL: TypeAlias = Literal[
    'DEBUG',
    'INFO',
    'WARNING',
    'CRITICAL',
    'ERROR'
]


class Config(pydantic_settings.BaseSettings):
    """Worker settings."""
    name: str
    db_uri: pydantic.SecretStr
    db_echo: bool = False
    hot_folder: Path | None = None
    cold_folder: Path | None = None
    save_hot: bool = True
    save_cold: bool = True
    log_level: LOG_LEVEL = 'INFO'
    log_debug: bool = False
    batch_size: int = 25
    prefix_size: int = 2
    media: Media = Media()
    manual_copy: Copy = Copy()
    timer_strategy: TimerStrategy = TimerStrategy()
    strategy: str = 'SignalStrategy'

    model_config = pydantic_settings.SettingsConfigDict(
        env_prefix='omoide_worker__',
        env_nested_delimiter='__'
    )

    @pydantic.model_validator(mode='after')
    def check_batch_size(self) -> 'Config':
        """Check."""
        if self.batch_size <= 0:
            msg = 'Batch size is too small (limit is 0)'
            raise ValueError(msg)

        if self.batch_size >= 10_000:
            msg = 'Batch size is too big (limit is 10 000)'
            raise ValueError(msg)

        return self

    @pydantic.model_validator(mode='after')
    def check_at_least_one_folder_given(self) -> 'Config':
        """Check."""
        if not any((self.hot_folder, self.cold_folder)):
            msg = ('At least one of hot-folder/cold-folder '
                   'variables must be given')
            raise ValueError(msg)

        return self

    @pydantic.model_validator(mode='after')
    def check_folders_are_adequate(self) -> 'Config':
        """Check."""
        if self.save_hot and not self.hot_folder:
            msg = ('You have to specify location '
                   'of the hot folder to save there')
            raise ValueError(msg)

        if self.save_cold and not self.cold_folder:
            msg = ('You have to specify location '
                   'of the cold folder to save there')
            raise ValueError(msg)

        return self

    @pydantic.model_validator(mode='after')
    def check_folders_exist(self) -> 'Config':
        """Check."""
        hot_exists = (self.hot_folder is not None
                      and self.hot_folder.exists())
        cold_exists = (self.cold_folder is not None
                       and self.cold_folder.exists())

        if not hot_exists and not cold_exists:
            msg = ('Both hot and cold folders do not exist: '
                   f'hot_folder={self.hot_folder}, '
                   f'cold_folder={self.cold_folder}')
            raise ValueError(msg)

        if self.save_hot and not hot_exists:
            msg = f'Hot folder does not exist: {self.hot_folder}'
            raise ValueError(msg)

        if self.save_cold and not cold_exists:
            msg = f'Cold folder does not exist: {self.cold_folder}'
            raise ValueError(msg)

        return self


def serialize(
        model: pydantic.BaseModel,
        do_not_serialize: frozenset = frozenset(('replication_formula',))
) -> str:
    """Convert config to human-readable string."""
    attributes: list[str] = []
    model_to_list(
        model=model,
        attributes=attributes,
        do_not_serialize=do_not_serialize,
        depth=0,
    )
    return '\n'.join(attributes)


def model_to_list(
        model: pydantic.BaseModel | dict[str, Any],
        attributes: list[str],
        do_not_serialize: frozenset,
        depth: int,
) -> None:
    """Convert each field to a list entry."""
    if isinstance(model, pydantic.BaseModel):
        payload = model.model_dump()
    else:
        payload = model

    prefix = '    ' * depth
    for key, value in payload.items():
        if isinstance(value, dict) and key not in do_not_serialize:
            line = f'{prefix}{key}:'
            attributes.append(line)
            model_to_list(value, attributes, do_not_serialize, depth + 1)
        else:
            line = f'{prefix}{key}={value!r}'
            attributes.append(line)


@cache
def get_config() -> Config:
    """Return instance of the config."""
    return Config()
