# -*- coding: utf-8 -*-
"""Preview related interfaces and objects.
"""
from pydantic import BaseModel

__all__ = [
    'Item',
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


class AccessStatus(BaseModel):
    """Status of an access and existence check."""
    exists: bool
    is_public: bool
    is_given: bool

    @property
    def does_not_exist(self) -> bool:
        """Return True if item does not exist."""
        return not self.exists

    @property
    def is_not_given(self) -> bool:
        """Return True if user cannot access this item."""
        return not self.is_public and not self.is_given
