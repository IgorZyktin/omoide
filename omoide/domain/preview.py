# -*- coding: utf-8 -*-
"""Preview related interfaces and objects.
"""
from typing import Mapping

from omoide.domain import utils, common

__all__ = [
    'ExtendedItem',
]


class ExtendedItem(common.Item):
    """Complete version of an item."""
    tags: list[str]
    permissions: list[str]

    @classmethod
    def from_map(cls, mapping: Mapping) -> 'ExtendedItem':
        """Convert from arbitrary format to model."""
        return cls(
            uuid=utils.as_str(mapping, 'uuid'),
            parent_uuid=utils.as_str(mapping, 'parent_uuid'),
            owner_uuid=utils.as_str(mapping, 'owner_uuid'),
            number=mapping['number'],
            name=mapping['name'],
            is_collection=mapping['is_collection'],
            content_ext=mapping['content_ext'],
            preview_ext=mapping['preview_ext'],
            thumbnail_ext=mapping['thumbnail_ext'],
            tags=mapping['tags'],
            permissions=mapping['permissions'],
        )
