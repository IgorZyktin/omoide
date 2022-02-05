# -*- coding: utf-8 -*-
"""Preview related interfaces and objects.
"""
from typing import Optional

from pydantic import BaseModel

from omoide.domain.common import Location, AccessStatus

__all__ = [
    'Item',
    'Result',
]


class Item(BaseModel):
    """Complete version of an item."""
    uuid: str
    parent_uuid: str | None
    owner_uuid: str | None
    number: int
    name: str
    is_collection: bool
    thumbnail_ext: str | None
    preview_ext: str | None
    content_ext: str | None
    tags: list[str]
    groups: list[str]

    @property
    def preview_location(self) -> str:
        """Return file system path segment that will allow to find file."""
        return f'{self.uuid[:2]}/{self.uuid}.{self.preview_ext}'

    @property
    def content_location(self) -> str:
        """Return file system path segment that will allow to find file."""
        return f'{self.uuid[:2]}/{self.uuid}.{self.content_ext}'

    @classmethod
    def empty(cls) -> 'Item':
        """User has no access to this item, return empty one."""
        return cls(
            uuid='',
            parent_uuid=None,
            owner_uuid=None,
            number=-1,
            name='',
            is_collection=False,
            thumbnail_ext=None,
            preview_ext=None,
            content_ext=None,
            tags=[],
            groups=[],
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
            parent_uuid=as_str('parent_uuid'),
            owner_uuid=as_str('owner_uuid'),
            number=raw_item['number'],
            name=raw_item['name'],
            is_collection=raw_item['is_collection'],
            thumbnail_ext=raw_item['thumbnail_ext'],
            preview_ext=raw_item['preview_ext'],
            content_ext=raw_item['content_ext'],
            tags=raw_item['tags'],
            groups=raw_item['permissions'],
        )
    # -------------------------------------------------------------------------


class Result(BaseModel):
    """Complete output of Preview request."""
    access: AccessStatus
    location: Location
    item: Optional[Item]
    neighbours: list[str]
