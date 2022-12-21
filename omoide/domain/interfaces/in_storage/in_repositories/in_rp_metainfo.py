# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on metainfo records.
"""
import abc
import datetime
from typing import Collection
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
    async def increase_known_tags_for_known_user(
            self,
            user_uuid: UUID,
            tags: list[str],
    ) -> None:
        """Increase counters for known tags using this item."""

    @abc.abstractmethod
    async def decrease_known_tags_for_known_user(
            self,
            user_uuid: UUID,
            tags: list[str],
    ) -> None:
        """Decrease counters for known tags using this item."""

    @abc.abstractmethod
    async def drop_unused_tags_for_known_user(
            self,
            user_uuid: UUID,
    ) -> None:
        """Drop tags with counter less of equal to 0."""

    @abc.abstractmethod
    async def increase_known_tags_for_anon_user(
            self,
            tags: list[str],
    ) -> None:
        """Increase counters for known tags using this item."""

    @abc.abstractmethod
    async def decrease_known_tags_for_anon_user(
            self,
            tags: list[str],
    ) -> None:
        """Decrease counters for known tags using this item."""

    @abc.abstractmethod
    async def drop_unused_tags_for_anon_user(
            self,
    ) -> None:
        """Drop tags with counter less of equal to 0."""

    @abc.abstractmethod
    async def mark_metainfo_updated(
            self,
            uuid: UUID,
            now: datetime.datetime,
    ) -> None:
        """Set last updated at given tine for the item."""

    @abc.abstractmethod
    async def start_long_job(
            self,
            name: str,
            user_uuid: UUID,
            target_uuid: UUID,
            added: Collection[str],
            deleted: Collection[str],
            status: str,
            started: datetime.datetime,
            extras: dict[str, int | float | bool | str | None],
    ) -> int:
        """Start long job."""

    @abc.abstractmethod
    async def finish_long_job(
            self,
            id: int,
            status: str,
            duration: float,
            operations: int,
    ) -> None:
        """Finish long job."""
