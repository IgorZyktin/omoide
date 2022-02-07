# -*- coding: utf-8 -*-
"""Domain utility functions.
"""
from typing import Mapping, Optional


def as_str(mapping: Mapping, key: str) -> Optional[str]:
    """Extract optional."""
    value = mapping[key]
    if value is None:
        return None
    return str(value)
