# -*- coding: utf-8 -*-
"""Use case for preview.
"""
from uuid import UUID

from omoide import domain
from omoide.domain import interfaces, exceptions


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
        async with self._repo.transaction():
            access = await self._repo.check_access(user, uuid)

            if access.does_not_exist:
                raise exceptions.NotFound(f'Item {uuid} does not exist')

            if access.is_not_given:
                if user.is_anon():
                    raise exceptions.Unauthorized(
                        f'Anon user has no access to {uuid}'
                    )
                else:
                    raise exceptions.Forbidden(
                        f'User {user.uuid} ({user.name}) '
                        f'has no access to {uuid}'
                    )

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
