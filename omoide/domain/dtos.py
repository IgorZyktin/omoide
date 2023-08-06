"""Data transfer objects.
"""
from pydantic import ConfigDict, BaseModel

__all__ = [
    'Obligation',
]


class BaseDTO(BaseModel):
    """Immutable model that does not support arbitrary attributes."""
    model_config = ConfigDict()


class Obligation(BaseDTO):
    """Prerequisite for execution."""
    max_results: int
