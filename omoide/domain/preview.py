# -*- coding: utf-8 -*-
"""Preview related interfaces and objects.
"""
from typing import Optional, Mapping

from pydantic import BaseModel

from omoide.domain import common

__all__ = [
    'ExtendedItem',
    'Result',
]


class ExtendedItem(common.Item):
    """Complete version of an item."""
    tags: list[str]
    permissions: list[str]

    @classmethod
    def from_map(cls, mapping: Mapping) -> 'ExtendedItem':
        """Convert from arbitrary format to model."""
        return cls(
            uuid=common.as_str(mapping, 'uuid'),
            parent_uuid=common.as_str(mapping, 'parent_uuid'),
            owner_uuid=common.as_str(mapping, 'owner_uuid'),
            number=mapping['number'],
            name=mapping['name'],
            is_collection=mapping['is_collection'],
            content_ext=mapping['content_ext'],
            preview_ext=mapping['preview_ext'],
            thumbnail_ext=mapping['thumbnail_ext'],
            tags=mapping['tags'],
            permissions=mapping['permissions'],
        )


class Result(BaseModel):
    """Complete output of Preview request."""
    access: common.AccessStatus
    location: common.Location
    item: Optional[ExtendedItem]
    neighbours: list[str]
