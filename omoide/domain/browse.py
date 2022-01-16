# -*- coding: utf-8 -*-
"""Preview related interfaces and objects.
"""
from pydantic import BaseModel

__all__ = [
    'AccessStatus',
    'Result',
]


class SimpleItem(BaseModel):
    """Primitive version of an item."""
    owner_uuid: str | None
    uuid: str
    is_collection: bool
    name: str
    ext: str | None

    @property
    def location(self) -> str:
        """Return file system path segment that will allow to find file."""
        return f'{self.uuid[:2]}/{self.uuid}.{self.ext}'


class Result(BaseModel):
    """Result of a search request."""
    page: int
    total_items: int
    total_pages: int
    items: list[SimpleItem]


class AccessStatus(BaseModel):
    """Status of an access and existence check."""
    exists: bool
    is_public: bool
    is_given: bool

    @property
    def does_not_exist(self) -> bool:
        """Return True if item does not exist."""
        return not self.exists

    @property
    def is_not_given(self) -> bool:
        """Return True if user cannot access this item."""
        return not self.is_public and not self.is_given


class Query(BaseModel):
    """User search query."""
    tags_include: list[str]
    tags_exclude: list[str]
    page: int
    items_per_page: int = 10
