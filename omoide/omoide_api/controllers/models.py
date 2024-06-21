"""Web level API models.
"""
from typing import Any

from pydantic import BaseModel


class UserOutput(BaseModel):
    """Simple user format."""
    uuid: str
    name: str
    extra: dict[str, Any]
