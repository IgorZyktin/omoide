# -*- coding: utf-8 -*-
"""Application settings.
"""
import os
from typing import Optional

from pydantic import BaseSettings, SecretStr


class Config(BaseSettings):
    """Application settings."""
    db_url: SecretStr
    injection: str = ''
    env: str = 'dev'
    host: str = '0.0.0.0'

    class Config:
        env_prefix = 'omoide_'


_active_config: Optional[Config] = None


def clear_env_on_prod(given_config: Config) -> None:
    """Clear env before start."""
    if given_config.env == 'prod':
        os.environ.clear()
        os.environb.clear()


def init(given_config: Optional[Config] = None) -> Config:
    """Generate new config instance."""
    global _active_config

    if given_config is None:
        _active_config = Config()
        clear_env_on_prod(_active_config)
    else:
        _active_config = given_config
    return _active_config


def get_config() -> Config:
    """Get instance of active config."""
    if _active_config is None:
        raise RuntimeError('No active config')
    return _active_config
