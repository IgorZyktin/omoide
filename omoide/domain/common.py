# -*- coding: utf-8 -*-
"""Models that used in more than one place.
"""
from datetime import datetime
from typing import Iterator
from typing import Literal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from omoide import domain

__all__ = [
    'Item',
    'PositionedItem',
    'PositionedByUserItem',
    'Location',
    'AccessStatus',
    'Query',
    'SingleResult',
    'SimpleLocation',
    'ComplexLocation',
    'Media',
    'EXIF',
    'NewPermissions',
    'Metainfo',
    'Aim',
    'SpaceUsage',
]


class Item(BaseModel):
    """Model of a standard item."""
    uuid: UUID
    parent_uuid: Optional[UUID]
    owner_uuid: UUID
    number: int
    name: str
    is_collection: bool
    content_ext: Optional[str]
    preview_ext: Optional[str]
    thumbnail_ext: Optional[str]
    tags: list[str] = []
    permissions: list[UUID] = []


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


class Media(BaseModel):
    """Transient content fot the item."""
    id: int
    owner_uuid: UUID
    item_uuid: UUID
    created_at: datetime
    processed_at: Optional[datetime]
    content: bytes
    ext: str
    target_folder: Literal['content', 'preview', 'thumbnail']
    replication: dict[str, dict]
    error: str
    attempts: int


class EXIF(BaseModel):
    """Exif media information."""
    item_uuid: UUID
    exif: dict[str, str | float | int | bool | None | list | dict]


class NewPermissions(BaseModel):
    """Input info for new permissions."""
    apply_to_parents: bool
    apply_to_children: bool
    override: bool
    permissions_before: set[UUID]
    permissions_after: set[UUID]

    @property
    def added(self) -> set[UUID]:
        """Return list of added permissions."""
        return set(self.permissions_after - self.permissions_before)

    @property
    def removed(self) -> set[UUID]:
        """Return list of removed permissions."""
        return set(self.permissions_before - self.permissions_after)

    @property
    def combined(self) -> set[UUID]:
        """Return all permissions."""
        return set(self.permissions_before | self.permissions_after)

    def apply_delta(self, item_permissions: set[UUID]) -> set[UUID]:
        """Apply addition and subtraction of items."""
        _result = set(item_permissions)
        _result = _result - self.removed
        _result = _result | self.added
        return _result


class Metainfo(BaseModel):
    """Metainfo for item."""
    item_uuid: UUID

    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    user_time: Optional[datetime]

    width: Optional[int]
    height: Optional[int]
    duration: Optional[float]
    resolution: Optional[float]
    media_type: Optional[str]

    author: Optional[str]
    author_url: Optional[str]
    saved_from_url: Optional[str]
    description: Optional[str]

    extras: dict

    content_size: Optional[int]
    preview_size: Optional[int]
    thumbnail_size: Optional[int]


class Aim(BaseModel):
    """Object that describes user's desired output."""
    query: Query
    ordered: bool
    nested: bool
    paged: bool
    page: int
    last_seen: int
    items_per_page: int

    @property
    def offset(self) -> int:
        """Return offset from start of the result block."""
        return self.items_per_page * (self.page - 1)

    def calc_total_pages(self, total_items: int) -> int:
        """Calculate how many pages we need considering this query."""
        return int(total_items / (self.items_per_page or 1))

    def using(
            self,
            **kwargs,
    ) -> 'Aim':
        """Create new instance with given params."""
        values = self.dict()
        values.update(kwargs)
        return type(self)(**kwargs)

    def url_safe(self) -> dict:
        """Return dict that can be converted to URL."""
        params = self.dict()
        params['q'] = self.query.raw_query
        params.pop('query', None)
        return params


class SingleResult(BaseModel):
    """Result of a request for a single item."""
    item: Item
    aim: Aim
    location: Location
    neighbours: list[UUID]


class SpaceUsage(BaseModel):
    """Total size of user data."""
    uuid: UUID
    content_size: int
    preview_size: int
    thumbnail_size: int

    @classmethod
    def empty(cls, uuid: UUID) -> 'SpaceUsage':
        """Return empty result."""
        return cls(
            uuid=uuid,
            content_size=0,
            preview_size=0,
            thumbnail_size=0,
        )
