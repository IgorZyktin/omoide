# -*- coding: utf-8 -*-
"""Core logic of the base repository.
"""
import abc
from typing import Any, Optional

from omoide import domain
from omoide.domain import interfaces


class BaseRepositoryLogic(interfaces.AbsRepository, abc.ABC):
    """Core logic of the base repository."""

    def __init__(self, db) -> None:
        """Initialize instance."""
        self.db = db

    def transaction(self) -> Any:
        """Start transaction."""
        return self.db.transaction()

    async def get_location(
            self,
            item_uuid: str,
            details: domain.Details,
    ) -> Optional[domain.Location]:
        """Return Location of the item."""
        current_item = await self.get_item(item_uuid)

        if current_item is None:
            return None

        owner = await self.get_user(current_item.owner_uuid)

        if owner is None:
            return None

        ancestors = await self._get_ancestors(current_item, details)

        if ancestors:
            positioned_owner = await self.get_positioned_by_user(
                owner, ancestors[0].item, details)
        else:
            positioned_owner = await self.get_positioned_by_user(
                owner, current_item, details)

        return domain.Location(
            owner=positioned_owner,
            items=ancestors,
            current_item=current_item,
        )

    async def _get_ancestors(
            self,
            item: domain.Item,
            details: domain.Details,
    ) -> list[domain.PositionedItem]:
        """Return list of positioned ancestors of given item."""
        ancestors = []

        item_uuid = item.parent_uuid
        child_uuid = item.uuid

        while True:
            if item_uuid is None:
                break

            ancestor = await self.get_item_with_position(
                item_uuid=item_uuid,
                child_uuid=child_uuid,
                details=details,
            )

            if ancestor is None:
                break

            ancestors.append(ancestor)
            item_uuid = ancestor.item.parent_uuid
            child_uuid = ancestor.item.uuid

        ancestors.reverse()
        return ancestors
