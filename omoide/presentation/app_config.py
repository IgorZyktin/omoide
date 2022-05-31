# -*- coding: utf-8 -*-
"""Application settings.
"""
from typing import Optional

from pydantic import BaseSettings, BaseModel


class App(BaseModel):
    """Settings for the app itself."""
    host: str = '0.0.0.0'
    port: int = 8080
    debug: bool = False
    reload: bool = False
    injection: str = ''


class Config(BaseSettings):
    """Application settings."""
    db_url: str
    env: str = 'dev'
    app: App = App()

    class Config:
        env_prefix = 'omoide_'
        env_nested_delimiter = '__'


_active_config: Optional[Config] = None


def init(given_config: Optional[Config] = None) -> Config:
    """Generate new config instance."""
    global _active_config

    if given_config is None:
        _active_config = Config()
    else:
        _active_config = given_config
    return _active_config


def get_config() -> Config:
    """Get instance of active config."""
    if _active_config is None:
        raise RuntimeError('No active config')
    return _active_config
