# -*- coding: utf-8 -*-
"""Business logic models.
"""
from dataclasses import dataclass
from typing import Optional

from omoide.infra import impl


class DomainModel:
    """Base class for all domain models."""


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
class EXIF(DomainModel):
    """Exif media information."""
    item_uuid: impl.UUID
    exif: impl.JSON
