# -*- coding: utf-8 -*-
"""Use case for preview.
"""
from typing import Optional

from omoide import domain
from omoide.domain import interfaces


class PreviewUseCase:
    """Use case for preview."""

    def __init__(self, repo: interfaces.AbsPreviewRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: domain.User,
            item_uuid: str,
            details: domain.Details,
    ) -> tuple[domain.AccessStatus, Optional[domain.SingleResult]]:
        """Return preview model suitable for rendering."""
        async with self._repo.transaction():
            access = await self._repo.check_access(user, item_uuid)

            if access.is_not_given:
                result = None

            else:
                location = await self._repo.get_location(user,
                                                         item_uuid,
                                                         details)
                item = await self._repo.get_extended_item(item_uuid)

                if user.is_anon():
                    neighbours = await self._repo.get_neighbours(
                        item_uuid=item_uuid,
                    )
                else:
                    neighbours = await self._repo.get_specific_neighbours(
                        user=user,
                        item_uuid=item_uuid,
                    )

                result = domain.SingleResult(
                    item=item,
                    details=details,
                    location=location,
                    neighbours=neighbours,
                )

        return access, result
