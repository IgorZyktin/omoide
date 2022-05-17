# -*- coding: utf-8 -*-
"""Use case for preview.
"""
from uuid import UUID

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
            uuid: UUID,
            details: domain.Details,
    ) -> domain.SingleResult:
        """Return preview model suitable for rendering."""
        await self._repo.assert_has_access(user, uuid)

        async with self._repo.transaction():
            location = await self._repo.get_location(user, uuid, details)
            item = await self._repo.get_extended_item(uuid)

            if user.is_anon():
                neighbours = await self._repo.get_neighbours(
                    item_uuid=uuid,
                )
            else:
                neighbours = await self._repo.get_specific_neighbours(
                    user=user,
                    item_uuid=uuid,
                )

            result = domain.SingleResult(
                item=item,
                details=details,
                location=location,
                neighbours=neighbours,
            )

        return result
