"""Models that used in more than one place."""

from typing import Callable
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from omoide import const

__all__ = [
    'Item',
    'Query',
    'Aim',
]


class Item(BaseModel):
    """Model of a standard item."""
    uuid: UUID
    parent_uuid: Optional[UUID] = None
    owner_uuid: UUID
    number: int
    name: str
    is_collection: bool
    content_ext: Optional[str] = None
    preview_ext: Optional[str] = None
    thumbnail_ext: Optional[str] = None
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
    original_ext: Optional[str] = None
    set_callback: Callable[[Optional[str]], None]

    @property
    def ext(self) -> Optional[str]:
        """Return extension of the file."""
        return self.original_ext

    @ext.setter
    def ext(self, new_ext: Optional[str]) -> None:
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
