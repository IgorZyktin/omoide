# -*- coding: utf-8 -*-
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

import omoide.domain.models

__all__ = [
    'SimpleItem',
    'COPIED_COVER_FROM',
    'CONTENT',
    'PREVIEW',
    'THUMBNAIL',
    'MEDIA_TYPE',
    'MEDIA_TYPES',
]

from omoide.domain import models

COPIED_COVER_FROM: Literal['copied_cover_from'] = 'copied_cover_from'
CONTENT: Literal['content'] = 'content'
PREVIEW: Literal['preview'] = 'preview'
THUMBNAIL: Literal['thumbnail'] = 'thumbnail'
MEDIA_TYPE = Literal['content', 'preview', 'thumbnail']
MEDIA_TYPES: list[MEDIA_TYPE] = [CONTENT, PREVIEW, THUMBNAIL]


# class Item(BaseModel):
#     """Model of a standard item."""
#     uuid: UUID
#     parent_uuid: Optional[UUID]
#     owner_uuid: UUID
#     number: int
#     name: str
#     is_collection: bool
#     content_ext: Optional[str]
#     preview_ext: Optional[str]
#     thumbnail_ext: Optional[str]
#     tags: list[str] = []
#     permissions: list[UUID] = []
#
#     def get_generic(self) -> dict[MEDIA_TYPE, 'ItemGeneric']:
#         """Proxy that helps with content/preview/thumbnail."""
#         return {
#             CONTENT: ItemGeneric(
#                 media_type=CONTENT,
#                 original_ext=self.content_ext,
#                 set_callback=lambda ext: setattr(self, 'content_ext', ext),
#             ),
#             PREVIEW: ItemGeneric(
#                 media_type=PREVIEW,
#                 original_ext=self.preview_ext,
#                 set_callback=lambda ext: setattr(self, 'preview_ext', ext),
#             ),
#             THUMBNAIL: ItemGeneric(
#                 media_type=THUMBNAIL,
#                 original_ext=self.thumbnail_ext,
#                 set_callback=lambda ext: setattr(self, 'thumbnail_ext', ext),
#             ),
#         }


class ItemGeneric(BaseModel):
    """Wrapper that helps with different item fields."""
    media_type: MEDIA_TYPE
    original_ext: Optional[str]
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
