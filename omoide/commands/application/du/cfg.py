# -*- coding: utf-8 -*-
"""Command configuration.
"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import SecretStr


class Config(BaseModel):
    """Command configuration."""
    db_url: SecretStr
    only_user: Optional[UUID]
