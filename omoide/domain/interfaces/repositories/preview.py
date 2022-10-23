# -*- coding: utf-8 -*-
"""Repository that performs all preview queries.
"""
import abc
from uuid import UUID

from omoide import domain
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
    async def get_neighbours(
            self,
            uuid: UUID,
    ) -> list[UUID]:
        """Return uuids of all the neighbours for given item UUID."""

    @abc.abstractmethod
    async def get_specific_neighbours(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> list[UUID]:
        """Return uuids of all the neighbours (which we have access to)."""
