"""Models that used in more than one place."""

import abc
import enum
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from omoide import const
from omoide import exceptions

__all__ = [
    'Item',
    'Query',
    'Aim',
    'OperationStatus',
    'SerialOperation',
]


class Item(BaseModel):
    """Model of a standard item."""

    uuid: UUID
    parent_uuid: UUID | None = None
    owner_uuid: UUID
    number: int
    name: str
    is_collection: bool
    content_ext: str | None = None
    preview_ext: str | None = None
    thumbnail_ext: str | None = None
    tags: list[str] = []
    permissions: list[UUID] = []

    def __str__(self) -> str:
        """Return textual representation."""
        name = type(self).__name__
        return f'<{name} {self.uuid} {self.name}>'

    def get_generic(self) -> dict[const.MEDIA_TYPE, 'ItemGeneric']:
        """Proxy that helps with content/preview/thumbnail."""
        return {
            const.CONTENT: ItemGeneric(
                media_type=const.CONTENT,
                original_ext=self.content_ext,
                set_callback=lambda ext: setattr(self, 'content_ext', ext),
            ),
            const.PREVIEW: ItemGeneric(
                media_type=const.PREVIEW,
                original_ext=self.preview_ext,
                set_callback=lambda ext: setattr(self, 'preview_ext', ext),
            ),
            const.THUMBNAIL: ItemGeneric(
                media_type=const.THUMBNAIL,
                original_ext=self.thumbnail_ext,
                set_callback=lambda ext: setattr(self, 'thumbnail_ext', ext),
            ),
        }


class ItemGeneric(BaseModel):
    """Wrapper that helps with different item fields."""

    media_type: const.MEDIA_TYPE
    original_ext: str | None = None
    set_callback: Callable[[str | None], None]

    @property
    def ext(self) -> str | None:
        """Return extension of the file."""
        return self.original_ext

    @ext.setter
    def ext(self, new_ext: str | None) -> None:
        """Return extension of the file."""
        self.set_callback(new_ext)
        self.original_ext = new_ext


class Query(BaseModel):
    """User search query."""

    raw_query: str
    tags_include: list[str]
    tags_exclude: list[str]

    def __bool__(self) -> bool:
        """Return True if query has tags to search."""
        return any((self.tags_include, self.tags_exclude))


class Aim(BaseModel):
    """Object that describes user's desired output."""

    query: Query
    order: const.ORDER_TYPE
    collections: bool
    direct: bool
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
        values = self.model_dump()
        values.update(kwargs)
        return type(self)(**kwargs)

    def url_safe(self) -> dict:
        """Return dict that can be converted to URL."""
        params = self.model_dump()
        params['q'] = self.query.raw_query
        params.pop('query', None)
        return params


ALL_OPERATIONS: dict[str, type['SerialOperation']] = {}


class OperationStatus(enum.StrEnum):
    """Possible statuses for operation."""

    CREATED = 'created'
    PROCESSING = 'processing'
    DONE = 'done'
    FAILED = 'failed'

    def __str__(self) -> str:
        """Return textual representation."""
        return f'<{self.name.lower()}>'


@dataclass
class SerialOperation(abc.ABC):
    """Base class for all serial operations."""

    id: int
    worker_name: str
    status: OperationStatus
    extras: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    ended_at: datetime | None
    log: str | None
    name: str = 'operation'

    def __init_subclass__(cls, *args: Any, **kwargs: Any) -> None:
        """Store descendant."""
        super().__init_subclass__(*args, **kwargs)
        ALL_OPERATIONS[cls.name] = cls

    @staticmethod
    def from_name(**kwargs: Any) -> 'SerialOperation':
        """Create specific instance type."""
        name = kwargs['name']
        class_ = ALL_OPERATIONS.get(name)
        if class_ is None:
            raise exceptions.UnknownSerialOperationError(name=name)

        return class_(**kwargs)

    @staticmethod
    def get_all_possible_operations() -> set[str]:
        """Return set of names for all descendants."""
        return set(ALL_OPERATIONS.keys())

    @abc.abstractmethod
    async def execute(self, **kwargs: Any) -> bool:
        """Perform workload."""

    @property
    def duration(self) -> float:
        """Get execution duration."""
        if self.started_at is None or self.ended_at is None:
            return 0.0
        return (self.ended_at - self.started_at).total_seconds()
