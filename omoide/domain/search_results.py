# -*- coding: utf-8 -*-
"""Search result containers.
"""
from pydantic import BaseModel


class SimpleItem(BaseModel):
    """Primitive version of an item."""
    owner_uuid: str
    uuid: str
    is_collection: bool
    name: str
    ext: str | None


class SearchResult(BaseModel):
    """Output of a regular search request."""
    is_random: bool
    page: int
    total_items: int
    total_pages: int
    items: list[SimpleItem]
