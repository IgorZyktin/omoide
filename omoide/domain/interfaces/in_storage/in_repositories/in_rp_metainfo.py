# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on metainfo records.
"""
import abc
import datetime
from typing import Any
from typing import Collection, Sequence
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
    async def read_children_to_download(
            self,
            user: domain.User,
            item: domain.Item,
    ) -> Sequence[list[dict[str, UUID | str | int]]]:
        """Return some components of the given item children with metainfo."""

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
    async def apply_new_known_tags(
            self,
            users: Collection[domain.User],
            tags_added: Collection[str],
            tags_deleted: Collection[str],
    ) -> None:
        """Update counters for known tags."""

    @abc.abstractmethod
    async def drop_unused_tags(
            self,
            users: Collection[domain.User],
            public_users: set[UUID],
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
    async def update_metainfo_extras(
            self,
            uuid: UUID,
            new_extras: dict[str, None | int | float | str | bool],
    ) -> None:
        """Add new data to extras."""

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
            error: str,
    ) -> None:
        """Finish long job."""
