# -*- coding: utf-8 -*-
"""Models that used in more than one place.
"""
import typing
from datetime import datetime
from typing import Optional, Mapping, Iterator
from uuid import UUID

from pydantic import BaseModel

from omoide import domain
from omoide.domain import utils

__all__ = [
    'Item',
    'PositionedItem',
    'PositionedByUserItem',
    'Location',
    'AccessStatus',
    'Query',
    'Details',
    'Results',
    'SingleResult',
    'SimpleLocation',
    'ComplexLocation',
    'Media',
    'EXIF',
    'Meta',
]


class Item(BaseModel):
    """Model of a standard item."""
    uuid: UUID
    parent_uuid: Optional[str]
    owner_uuid: str
    number: int
    name: str
    is_collection: bool
    content_ext: Optional[str]
    preview_ext: Optional[str]
    thumbnail_ext: Optional[str]
    tags: list[str]
    permissions: list[str]

    @property
    def content_path(self) -> str:
        """Return file system path segment that will allow to find file."""
        return f'{str(self.uuid)[:2]}/{self.uuid}.{self.content_ext}'

    @property
    def preview_path(self) -> str:
        """Return file system path segment that will allow to find file."""
        return f'{str(self.uuid)[:2]}/{self.uuid}.{self.preview_ext}'

    @property
    def thumbnail_path(self) -> str:
        """Return file system path segment that will allow to find file."""
        return f'{str(self.uuid)[:2]}/{self.uuid}.{self.thumbnail_ext}'

    @classmethod
    def from_map(cls, mapping: Mapping) -> 'Item':
        """Convert from arbitrary format to model."""
        # TODO - damn asyncpg tries to bee too smart
        _mapping = dict(zip(mapping.keys(), mapping.values()))
        return cls(
            uuid=utils.as_str(_mapping, 'uuid'),
            parent_uuid=utils.as_str(_mapping, 'parent_uuid'),
            owner_uuid=utils.as_str(_mapping, 'owner_uuid'),
            number=_mapping['number'],
            name=_mapping['name'],
            is_collection=_mapping['is_collection'],
            content_ext=_mapping['content_ext'],
            preview_ext=_mapping['preview_ext'],
            thumbnail_ext=_mapping['thumbnail_ext'],
            tags=_mapping.get('tags', []) or [],
            permissions=_mapping.get('permissions', []) or [],
        )


class PositionedItem(BaseModel):
    """Primitive version of an item with position information."""
    position: int
    total_items: int
    items_per_page: int
    item: Item

    @property
    def page(self) -> int:
        """Return page number for this item in parent's collection."""
        return self.position // self.items_per_page + 1


class PositionedByUserItem(BaseModel):
    """Same as PositionedItem but according to user catalogue."""
    user: domain.User
    position: int
    total_items: int
    items_per_page: int
    item: Item

    @property
    def page(self) -> int:
        """Return page number for this item in parent's collection."""
        return self.position // self.items_per_page + 1


class Location(BaseModel):
    """Path-like sequence of parents for specific item."""
    owner: domain.User
    items: list[PositionedItem]
    current_item: Optional[Item]

    def __bool__(self) -> bool:
        """Return True if location is not empty."""
        return (self.owner is not None) and bool(self.items)

    def __iter__(self) -> Iterator[PositionedItem]:  # type: ignore
        """Iterate over items."""
        return iter(self.items)


class SimpleLocation(BaseModel):
    """Path-like sequence of parents for specific item."""
    items: list[Item]

    def __bool__(self) -> bool:
        """Return True if location is not empty."""
        return bool(self.items)

    def __iter__(self) -> Iterator[Item]:  # type: ignore
        """Iterate over items."""
        return iter(self.items)


class ComplexLocation(BaseModel):
    """Path-like sequence of parents for specific item."""
    owner: domain.User
    items: list[PositionedItem]
    current_item: Optional[Item]

    def __bool__(self) -> bool:
        """Return True if location is not empty."""
        return (self.owner is not None) and bool(self.items)

    def __iter__(self) -> Iterator[PositionedItem]:  # type: ignore
        """Iterate over items."""
        return iter(self.items)


class AccessStatus(BaseModel):
    """Status of an access and existence check."""
    exists: bool
    is_public: bool
    is_permitted: bool
    is_owner: bool

    @property
    def does_not_exist(self) -> bool:
        """Return True if item does not exist."""
        return not self.exists

    @property
    def is_given(self) -> bool:
        """Return True if user can access this item."""
        return any([
            self.is_public,
            self.is_owner,
            self.is_permitted,
        ])

    @property
    def is_not_given(self) -> bool:
        """Return True if user cannot access this item."""
        return not self.is_given

    @property
    def is_not_owner(self) -> bool:
        """Return True if user is not owner of the item."""
        return not self.is_owner

    @classmethod
    def not_found(cls) -> 'AccessStatus':
        """Item does not exist."""
        return cls(
            exists=False,
            is_public=False,
            is_permitted=False,
            is_owner=False,
        )


class Query(BaseModel):
    """User search query."""
    raw_query: str
    tags_include: list[str]
    tags_exclude: list[str]

    def __bool__(self) -> bool:
        """Return True if query has tags to search."""
        return any((self.tags_include, self.tags_exclude))


class Details(BaseModel):
    """Additional request parameters."""
    page: int
    anchor: int
    items_per_page: int
    items_per_page_async: int = -1

    def at_page(self, page: int, anchor: int) -> 'Details':
        """Return details with different page."""
        return type(self)(
            page=page,
            anchor=anchor,
            items_per_page=self.items_per_page,
            items_per_page_async=self.items_per_page_async,
        )

    @property
    def offset(self) -> int:
        """Return offset from start of the result block."""
        return self.items_per_page * (self.page - 1)

    def calc_total_pages(self, total_items: int) -> int:
        """Calculate how many pages we need considering this query."""
        return int(total_items / (self.items_per_page or 1))


class Results(BaseModel):
    """Result of a search request."""
    item: Optional[Item]
    total_items: int
    total_pages: int
    items: list[Item]
    details: Details
    location: Optional[Location]

    @property
    def page(self) -> int:
        """Return current page number."""
        return self.details.page


class SingleResult(BaseModel):
    """Result of a request for a single item."""
    item: Item
    details: Details
    location: Location
    neighbours: list[UUID]


class Media(BaseModel):
    """Transient content fot the item."""
    item_uuid: UUID
    created_at: datetime
    processed_at: Optional[datetime]
    status: str
    content: bytes
    ext: str
    media_type: str

    @classmethod
    def from_map(cls, mapping: Mapping) -> 'Media':
        """Convert from arbitrary format to model."""
        return cls(
            item_uuid=utils.as_str(mapping, 'item_uuid'),
            created_at=mapping['created_at'],
            processed_at=mapping['processed_at'],
            status=mapping['status'],
            content=mapping['content'],
            ext=mapping['ext'],
            media_type=mapping['media_type'],
        )


class EXIF(BaseModel):
    """Exif media information."""
    item_uuid: UUID
    exif: dict[str, typing.Any]

    @classmethod
    def from_map(cls, mapping: Mapping) -> 'EXIF':
        """Convert from arbitrary format to model."""
        return cls(
            item_uuid=utils.as_str(mapping, 'item_uuid'),
            exif=mapping['exif'],
        )


class Meta(BaseModel):
    """Metainfo for item."""
    item_uuid: UUID
    meta: dict

    @classmethod
    def from_map(cls, mapping: Mapping) -> 'Meta':
        """Convert from arbitrary format to model."""
        return cls(
            item_uuid=utils.as_str(mapping, 'item_uuid'),
            meta=mapping['data'],
        )
