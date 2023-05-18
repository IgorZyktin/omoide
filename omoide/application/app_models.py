# -*- coding: utf-8 -*-
"""Application models for internal use.
"""
from dataclasses import asdict
from dataclasses import dataclass
from typing import Iterator
from typing import Optional

from omoide.domain import models
from omoide.infra import impl


class AppModel:
    """Base class for all app models."""


@dataclass
class Query(AppModel):
    """User search query."""
    raw_query: str
    tags_include: list[str]
    tags_exclude: list[str]

    def __bool__(self) -> bool:
        """Return True if query has tags to search."""
        return any((self.tags_include, self.tags_exclude))


@dataclass
class SpaceUsage(AppModel):
    """Total size of user data."""
    uuid: impl.UUID
    content_size: int
    preview_size: int
    thumbnail_size: int

    @classmethod
    def empty(cls, uuid: impl.UUID) -> 'SpaceUsage':
        """Return empty result."""
        return cls(
            uuid=uuid,
            content_size=0,
            preview_size=0,
            thumbnail_size=0,
        )


@dataclass
class Aim(AppModel):
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

    def using(self, **kwargs) -> 'Aim':
        """Create new instance with given params."""
        values = asdict(self)
        values.update(kwargs)
        return type(self)(**kwargs)

    def url_safe(self) -> dict:
        """Return dict that can be converted to URL."""
        params = asdict(self)
        params['q'] = self.query.raw_query
        params.pop('query', None)
        return params


@dataclass
class PositionedItem(AppModel):
    """Primitive version of an item with position information."""
    position: int
    total_items: int
    items_per_page: int
    item: models.Item

    @property
    def page(self) -> int:
        """Return page number for this item in parent's collection."""
        return self.position // self.items_per_page + 1


@dataclass
class PositionedByUserItem(AppModel):
    """Same as PositionedItem but according to user catalogue."""
    user: models.User
    position: int
    total_items: int
    items_per_page: int
    item: models.Item

    @property
    def page(self) -> int:
        """Return page number for this item in parent's collection."""
        return self.position // self.items_per_page + 1


@dataclass
class Location(AppModel):
    """Path-like sequence of parents for specific item."""
    owner: models.User
    items: list[PositionedItem]
    current_item: Optional[models.Item]

    def __bool__(self) -> bool:
        """Return True if location is not empty."""
        return (self.owner is not None) and bool(self.items)

    def __iter__(self) -> Iterator[PositionedItem]:  # type: ignore
        """Iterate over items."""
        return iter(self.items)


@dataclass
class SimpleLocation(AppModel):
    """Path-like sequence of parents for specific item."""
    items: list[models.Item]

    def __bool__(self) -> bool:
        """Return True if location is not empty."""
        return bool(self.items)

    def __iter__(self) -> Iterator[models.Item]:  # type: ignore
        """Iterate over items."""
        return iter(self.items)


@dataclass
class ComplexLocation(AppModel):
    """Path-like sequence of parents for specific item."""
    owner: models.User
    items: list[PositionedItem]
    current_item: Optional[models.Item]

    def __bool__(self) -> bool:
        """Return True if location is not empty."""
        return (self.owner is not None) and bool(self.items)

    def __iter__(self) -> Iterator[PositionedItem]:  # type: ignore
        """Iterate over items."""
        return iter(self.items)


@dataclass
class SingleResult(AppModel):
    """Result of a request for a single item."""
    item: models.Item
    metainfo: models.Metainfo
    aim: Aim
    location: Location
    neighbours: list[impl.UUID]
