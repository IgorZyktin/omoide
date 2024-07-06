"""Models that used in more than one place.
"""
from datetime import datetime
from typing import Callable
from typing import Iterator
from typing import Literal
from typing import Optional
from typing import TypedDict
from uuid import UUID

from pydantic import BaseModel

from omoide import models

__all__ = [
    'Item',
    'SimpleItem',
    'PositionedItem',
    'PositionedByUserItem',
    'Location',
    'AccessStatus',
    'Query',
    'SingleResult',
    'SimpleLocation',
    'ComplexLocation',
    'Metainfo',
    'Aim',
    'SpaceUsage',
    'CONTENT',
    'PREVIEW',
    'THUMBNAIL',
    'MEDIA_TYPE',
    'MEDIA_TYPES',
]

CONTENT: Literal['content'] = 'content'
PREVIEW: Literal['preview'] = 'preview'
THUMBNAIL: Literal['thumbnail'] = 'thumbnail'
MEDIA_TYPE = Literal['content', 'preview', 'thumbnail']
MEDIA_TYPES: list[MEDIA_TYPE] = [CONTENT, PREVIEW, THUMBNAIL]


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

    def get_generic(self) -> dict[MEDIA_TYPE, 'ItemGeneric']:
        """Proxy that helps with content/preview/thumbnail."""
        return {
            CONTENT: ItemGeneric(
                media_type=CONTENT,
                original_ext=self.content_ext,
                set_callback=lambda ext: setattr(self, 'content_ext', ext),
            ),
            PREVIEW: ItemGeneric(
                media_type=PREVIEW,
                original_ext=self.preview_ext,
                set_callback=lambda ext: setattr(self, 'preview_ext', ext),
            ),
            THUMBNAIL: ItemGeneric(
                media_type=THUMBNAIL,
                original_ext=self.thumbnail_ext,
                set_callback=lambda ext: setattr(self, 'thumbnail_ext', ext),
            ),
        }


class ItemGeneric(BaseModel):
    """Wrapper that helps with different item fields."""
    media_type: MEDIA_TYPE
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


class SimpleItem(TypedDict):
    """JSON compatible item."""
    uuid: str
    parent_name: Optional[str]
    number: int
    name: str
    href: str
    is_collection: bool
    thumbnail: str


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
    user: models.User
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
    owner: models.User
    items: list[PositionedItem]
    current_item: Optional[Item] = None

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
    owner: models.User
    items: list[PositionedItem]
    current_item: Optional[Item] = None

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


class Metainfo(BaseModel):
    """Metainfo for item."""
    item_uuid: UUID

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    user_time: datetime | None = None

    content_type: str | None = None

    author: str | None = None
    author_url: str | None = None
    saved_from_url: str | None = None
    description: str | None = None

    extras: dict

    content_size: int | None = None
    preview_size: int | None = None
    thumbnail_size: int | None = None

    content_width: int | None = None
    content_height: int | None = None
    preview_width: int | None = None
    preview_height: int | None = None
    thumbnail_width: int | None = None
    thumbnail_height: int | None = None


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
        values = self.model_dump()
        values.update(kwargs)
        return type(self)(**kwargs)

    def url_safe(self) -> dict:
        """Return dict that can be converted to URL."""
        params = self.model_dump()
        params['q'] = self.query.raw_query
        params.pop('query', None)
        return params


class SingleResult(BaseModel):
    """Result of a request for a single item."""
    item: Item
    metainfo: Metainfo
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
