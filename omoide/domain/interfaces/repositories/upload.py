# -*- coding: utf-8 -*-
"""Repository that handles media upload.
"""
import abc

from omoide import domain
from omoide.domain.interfaces.repositories.items import AbsItemsRepository


class AbsUploadRepository(AbsItemsRepository, abc.ABC):
    """Repository that handles media upload."""

    @abc.abstractmethod
    async def save_raw_media(
            self,
            payload: domain.RawMedia,
    ) -> bool:
        """Save given content to the DB."""
