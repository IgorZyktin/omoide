# -*- coding: utf-8 -*-
"""Application settings.
"""
from pydantic import BaseSettings


class Config(BaseSettings):
    """Application settings."""
    omoide_db_url: str
    omoide_injection: str = ''
    omoide_env: str = 'dev'


config = Config()
