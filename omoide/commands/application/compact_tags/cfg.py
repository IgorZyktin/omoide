"""Command configuration.
"""
from uuid import UUID

from pydantic import BaseModel
from pydantic import SecretStr


class Config(BaseModel):
    """Command configuration."""
    db_url: SecretStr
    only_users: list[UUID | str]
    log_every_item: bool
