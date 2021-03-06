# -*- coding: utf-8 -*-
"""Repository that performs all preview queries.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain import preview
from omoide.domain.interfaces.repositories.base import AbsRepository
from omoide.domain.interfaces.repositories.in_rp_items import (
    AbsItemsRepository
)


class AbsPreviewRepository(
    AbsItemsRepository,
    AbsRepository,
):
    """Repository that performs all preview queries."""

    @abc.abstractmethod
    async def get_extended_item(
            self,
            item_uuid: str,
    ) -> Optional[preview.ExtendedItem]:
        """Return instance of the item."""

    @abc.abstractmethod
    async def get_neighbours(self, item_uuid: str) -> list[UUID]:
        """Return uuids of all the neighbours."""

    @abc.abstractmethod
    async def get_specific_neighbours(
            self,
            user: domain.User,
            item_uuid: str,
    ) -> list[UUID]:
        """Return uuids of all the neighbours (which we have access to)."""
