# -*- coding: utf-8 -*-
"""Application settings.
"""
from pydantic import BaseSettings
from pydantic import SecretStr


class Config(BaseSettings):
    """Application settings."""
    db_url_app: SecretStr
    injection: str = ''
    env: str = 'dev'
    host: str = '0.0.0.0'
    prefix_size: int = 2
    penalty_wrong_password: float = 2.5

    class Config:
        env_prefix = 'omoide_'
