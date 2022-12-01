# -*- coding: utf-8 -*-
"""Meta configuration.
"""
from pydantic import BaseModel


class MetaConfig(BaseModel):
    """Meta configuration."""
    replication_formula: dict[str, bool]
