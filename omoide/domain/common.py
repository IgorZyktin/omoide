# -*- coding: utf-8 -*-
"""Models that used in more than one place.
"""
from pydantic import BaseModel


class SimpleUser(BaseModel):
    """Primitive version of User model."""
    uuid: str
    name: str

    @classmethod
    def empty(cls) -> 'SimpleUser':
        """User has no access to this info, return empty one."""
        return cls(
            uuid='',
            name='',
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
            name=raw_item['name'],
        )
    # -------------------------------------------------------------------------


class SimpleItem(BaseModel):
    """Primitive version of an item."""
    owner_uuid: str | None
    uuid: str
    is_collection: bool
    name: str
    ext: str | None

    @property
    def path(self) -> str:
        """Return file system path segment that will allow to find file."""
        return f'{self.uuid[:2]}/{self.uuid}.{self.ext}'

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
            owner_uuid=as_str('owner_uuid'),
            uuid=as_str('uuid'),
            is_collection=raw_item['is_collection'],
            name=raw_item['name'],
            ext=raw_item['ext'],
        )
    # -------------------------------------------------------------------------


class Location(BaseModel):
    """Path-like sequence of parents for specific item."""
    owner: SimpleUser | None
    items: list[SimpleItem]

    def __bool__(self) -> bool:
        """Return True if location is not empty."""
        return self.owner is not None and self.items

    @classmethod
    def empty(cls) -> 'Location':
        """User has no access to this location, return empty one."""
        return cls(
            owner=None,
            items=[],
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

    @classmethod
    def not_found(cls) -> 'AccessStatus':
        """Item does not exist."""
        return cls(
            exists=False,
            is_public=False,
            is_given=False,
        )
