# -*- coding: utf-8 -*-
"""Data transfer objects.
"""
from pydantic import ConfigDict, BaseModel

__all__ = [
    'GuessTag',
    'GuessResult',
    'Obligation',
]


class BaseDTO(BaseModel):
    """Immutable model that does not support arbitrary attributes."""
    model_config = ConfigDict()


class GuessTag(BaseDTO):
    """Arbitrary text entered by user that potentially can match with tag."""
    text: str


class GuessResult(BaseDTO):
    """Variants that can possibly match with user guess."""
    tag: str
    counter: str


class Obligation(BaseDTO):
    """Prerequisite for execution."""
    max_results: int
