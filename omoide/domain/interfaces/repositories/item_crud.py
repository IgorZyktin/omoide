# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on items and their data.
"""
import abc

from omoide import domain
from omoide.domain.interfaces.repositories.base import AbsRepository


class AbsItemCRUDRepository(AbsRepository, abc.ABC):
    """Repository that perform CRUD operations on items and their data."""

    @abc.abstractmethod
    async def save_raw_media(
            self,
            payload: domain.RawMedia,
    ) -> bool:
        """Save given content to the DB."""
