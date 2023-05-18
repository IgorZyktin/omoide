# -*- coding: utf-8 -*-
"""Repository that performs all preview queries.
"""
import abc
from uuid import UUID

import omoide.domain.models
from omoide import domain
from omoide.domain.interfaces.in_storage.in_repositories.in_rp_browse import \
    AbsBrowseRepository


class AbsPreviewRepository(
    AbsBrowseRepository,
):
    """Repository that performs all preview queries."""

    @abc.abstractmethod
    async def get_neighbours(
            self,
            user: omoide.domain.models.User,
            uuid: UUID,
    ) -> list[UUID]:
        """Return uuids of all the neighbours for given item UUID."""
