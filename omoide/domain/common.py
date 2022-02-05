# -*- coding: utf-8 -*-
"""Models that used in more than one place.
"""
from typing import Optional, Mapping

from pydantic import BaseModel


def _as_str(mapping: Mapping, key: str) -> str | None:
    """Extract optional."""
    value = mapping[key]
    if value is None:
        return None
    return str(value)


class SimpleUser(BaseModel):
    """Primitive version of User model."""
    uuid: str
    name: str

    @classmethod
    def empty(cls) -> 'SimpleUser':
        """User has no access to this info, return empty one."""
        return cls(
            uuid='',
            name='',
        )

    # -------------------------------------------------------------------------
    # TODO - hacky solutions, must get rid of UUID type
    @classmethod
    def from_row(cls, raw_item):
        """Convert from db format to required model."""

        def as_str(key: str) -> str | None:
            """Extract optional."""
            value = raw_item[key]
            if value is None:
                return None
            return str(value)

        return cls(
            uuid=as_str('uuid'),
            name=raw_item['name'],
        )
    # -------------------------------------------------------------------------


class Item(BaseModel):
    """Model of a standard item."""
    uuid: str
    parent_uuid: Optional[str]
    owner_uuid: str
    number: int
    name: str
    is_collection: bool
    content_ext: Optional[str]
    preview_ext: Optional[str]
    thumbnail_ext: Optional[str]

    @property
    def thumbnail_path(self) -> str:
        """Return file system path segment that will allow to find file."""
        return f'{self.uuid[:2]}/{self.uuid}.{self.thumbnail_ext}'

    @property
    def preview_path(self) -> str:
        """Return file system path segment that will allow to find file."""
        return f'{self.uuid[:2]}/{self.uuid}.{self.preview_ext}'

    @property
    def content_path(self) -> str:
        """Return file system path segment that will allow to find file."""
        return f'{self.uuid[:2]}/{self.uuid}.{self.content_ext}'

    @classmethod
    def from_map(cls, mapping: Mapping) -> 'Item':
        """Convert from arbitrary format to model."""
        return cls(
            uuid=_as_str(mapping, 'uuid'),
            parent_uuid=_as_str(mapping, 'parent_uuid'),
            owner_uuid=_as_str(mapping, 'owner_uuid'),
            number=mapping['number'],
            name=mapping['name'],
            is_collection=mapping['is_collection'],
            content_ext=mapping['content_ext'],
            preview_ext=mapping['preview_ext'],
            thumbnail_ext=mapping['thumbnail_ext'],
        )


class PositionedItem(BaseModel):
    """Primitive version of an item with position information."""
    position: int
    total_items: int
    item: Item


class Location(BaseModel):
    """Path-like sequence of parents for specific item."""
    owner: SimpleUser | None
    items: list[Item]

    def __bool__(self) -> bool:
        """Return True if location is not empty."""
        return self.owner is not None and self.items

    @classmethod
    def empty(cls) -> 'Location':
        """User has no access to this location, return empty one."""
        return cls(
            owner=None,
            items=[],
        )


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

    @classmethod
    def not_found(cls) -> 'AccessStatus':
        """Item does not exist."""
        return cls(
            exists=False,
            is_public=False,
            is_given=False,
        )


class Query(BaseModel):
    """User search query."""
    tags_include: list[str]
    tags_exclude: list[str]
    page: int
    items_per_page: int

    def __bool__(self) -> bool:
        """Return True if query has tags to search."""
        return any((
            self.tags_include,
            self.tags_exclude,
        ))

    @property
    def offset(self) -> int:
        """Return offset from start of the result block."""
        return self.items_per_page * (self.page - 1)

    def calc_total_pages(self, total_items: int) -> int:
        """Calculate how many pages we need considering this query."""
        return int(total_items / (self.items_per_page or 1))
