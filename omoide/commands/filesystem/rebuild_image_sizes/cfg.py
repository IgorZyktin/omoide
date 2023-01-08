# -*- coding: utf-8 -*-
"""Command configuration.
"""
from uuid import UUID

from pydantic import BaseModel
from pydantic import SecretStr


class Config(BaseModel):
    """Command configuration."""
    db_url: SecretStr
    hot_folder: str
    cold_folder: str
    only_users: list[UUID]
    log_every_item: bool
    only_corrupted: bool
    limit: int
    prefix_size: int = 2
