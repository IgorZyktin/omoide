# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on metainfo records.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_base


class AbsMetainfoRepository(in_rp_base.AbsBaseRepository):
    """Repository that perform CRUD operations on metainfo records."""

    @abc.abstractmethod
    async def create_empty_metainfo(
            self,
            user: domain.User,
            item: domain.Item,
    ) -> bool:
        """Create metainfo with blank fields."""

    @abc.abstractmethod
    async def read_metainfo(
            self,
            uuid: UUID,
    ) -> Optional[domain.Metainfo]:
        """Return Metainfo or None."""

    @abc.abstractmethod
    async def update_metainfo(
            self,
            user: domain.User,
            metainfo: domain.Metainfo,
    ) -> None:
        """Update metainfo and return true on success."""

    @abc.abstractmethod
    async def update_computed_tags(
            self,
            user: domain.User,
            item: domain.Item,
    ) -> None:
        """Update computed tags for this item."""

    @abc.abstractmethod
    async def update_computed_permissions(
            self,
            user: domain.User,
            item: domain.Item,
    ) -> None:
        """Update computed permissions for this item."""

    @abc.abstractmethod
    async def update_known_tags_for_known_user(
            self,
            user_uuid: UUID,
            item: domain.Item,
    ) -> None:
        """Update known tags using this item."""

    @abc.abstractmethod
    async def drop_unused_tags_for_known_user(
            self,
            user_uuid: UUID,
    ) -> None:
        """Drop tags with counter less of equal to 0."""

    @abc.abstractmethod
    async def update_known_tags_for_anon_user(
            self,
            item: domain.Item,
    ) -> None:
        """Update known tags using this item."""

    @abc.abstractmethod
    async def drop_unused_tags_for_anon_user(
            self,
            user_uuid: UUID,
    ) -> None:
        """Drop tags with counter less of equal to 0."""
