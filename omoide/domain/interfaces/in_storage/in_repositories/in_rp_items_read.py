# -*- coding: utf-8 -*-
"""Repository that performs basic read operations on items.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_base


class AbsItemsReadRepository(in_rp_base.AbsBaseRepository):
    """Repository that performs basic read operations on items."""

    @abc.abstractmethod
    async def check_access(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> domain.AccessStatus:
        """Check access to the Item with given UUID for the given User."""

    @abc.abstractmethod
    async def read_item(
            self,
            uuid: UUID,
    ) -> Optional[domain.Item]:
        """Return Item or None."""
