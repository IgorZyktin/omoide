# -*- coding: utf-8 -*-
"""Command configuration.
"""
from uuid import UUID

from pydantic import BaseModel
from pydantic import SecretStr


class Config(BaseModel):
    """Command configuration."""
    db_url: SecretStr
    only_users: list[UUID]
    log_every_item: bool
    api_endpoint: str
