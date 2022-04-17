# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on items and their data.
"""
import abc

from omoide import domain
from omoide.domain.interfaces.repositories.base import AbsRepository


class AbsItemCRUDRepository(AbsRepository, abc.ABC):
    """Repository that perform CRUD operations on items and their data."""

    @abc.abstractmethod
    async def create_root_item(
            self,
            user: domain.User,
            payload: domain.CreateItemPayload,
    ) -> domain.Item:
        """Create item without parent."""

    @abc.abstractmethod
    async def create_dependant_item(
            self,
            user: domain.User,
            payload: domain.CreateItemPayload,
    ) -> domain.Item:
        """Create item with parent."""
