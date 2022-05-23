# -*- coding: utf-8 -*-
"""Use case for items.
"""
from omoide import domain


class AppDeleteItemUseCase:
    """Use case for deleting an item."""

    async def execute(
            self,
            user: domain.User,
            raw_uuid: str,
    ) -> None:
        """Business logic."""
        await self._assert_has_access(user, uuid)
        # TODO(i.zyktin): add records to the zombies table
        return await self._repo.delete_item(uuid)
