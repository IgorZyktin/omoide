# -*- coding: utf-8 -*-
"""Command configuration.
"""
from pydantic import BaseModel
from pydantic import SecretStr


class Config(BaseModel):
    """Command configuration."""
    db_url: SecretStr
    anon: bool
    known: bool
