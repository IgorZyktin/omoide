# -*- coding: utf-8 -*-
"""User search query.
"""
from pydantic import BaseModel


class Query(BaseModel):
    """User search query."""
    raw_query: str
    tags_include: list[str]
    tags_exclude: list[str]
    page: int
    folded: bool

    def __bool__(self) -> bool:
        """Return True if query has tags to search."""
        return bool(self.tags_include) and bool(self.tags_exclude)
