# -*- coding: utf-8 -*-
"""Business logic models.
"""
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Literal
from typing import Optional

from omoide.infra import impl


class DomainModel:
    """Base class for all domain models."""


@dataclass
class AccessStatus(DomainModel):
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
        return any((
            self.is_public,
            self.is_owner,
            self.is_permitted,
        ))

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


@dataclass
class User(DomainModel):
    """User model."""
    uuid: Optional[impl.UUID]
    login: str
    password: str
    name: str
    root_item: Optional[impl.UUID]

    @property
    def is_registered(self) -> bool:
        """Return True if user is registered."""
        return self.uuid is not None

    @property
    def is_not_registered(self) -> bool:
        """Return True if user is anon."""
        return not self.is_registered

    @property
    def is_anon(self) -> bool:
        """Return True if user is anonymous."""
        return self.uuid is None

    @property
    def is_not_anon(self) -> bool:
        """Return True if user is registered one."""
        return not self.is_anon

    @classmethod
    def new_anon(cls) -> 'User':
        """Return new anon user."""
        return cls(
            uuid=None,
            login='',
            password='',
            name='anon',
            root_item=None,
        )


@dataclass
class Item(DomainModel):
    """Model of a standard item."""
    uuid: impl.UUID
    parent_uuid: Optional[impl.UUID]
    owner_uuid: impl.UUID
    number: int
    name: str
    is_collection: bool
    content_ext: Optional[str]
    preview_ext: Optional[str]
    thumbnail_ext: Optional[str]
    tags: list[str] = field(default_factory=list)
    permissions: list[impl.UUID] = field(default_factory=list)


@dataclass
class Metainfo(DomainModel):
    """Metainfo for item."""
    item_uuid: impl.UUID

    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    user_time: Optional[datetime]

    media_type: Optional[str]

    author: Optional[str]
    author_url: Optional[str]
    saved_from_url: Optional[str]
    description: Optional[str]

    extras: impl.SIMPLE_DICT

    content_size: Optional[int]
    preview_size: Optional[int]
    thumbnail_size: Optional[int]

    content_width: Optional[int]
    content_height: Optional[int]
    preview_width: Optional[int]
    preview_height: Optional[int]
    thumbnail_width: Optional[int]
    thumbnail_height: Optional[int]


@dataclass
class Media(DomainModel):
    """Transient content fot the item."""
    id: int
    owner_uuid: impl.UUID
    item_uuid: impl.UUID
    created_at: datetime
    processed_at: Optional[datetime]
    content: bytes
    ext: str
    target_folder: Literal['content', 'preview', 'thumbnail']
    replication: dict[str, dict]
    error: str
    attempts: int


@dataclass
class EXIF(DomainModel):
    """Exif media information."""
    item_uuid: impl.UUID
    exif: impl.SIMPLE_DICT
