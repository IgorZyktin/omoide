# -*- coding: utf-8 -*-
"""Use case for browse.
"""
from uuid import UUID

from omoide import domain
from omoide.domain import interfaces, exceptions


class BrowseUseCase:
    """Use case for browse."""

    def __init__(self, repo: interfaces.AbsBrowseRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: domain.User,
            item_uuid: UUID,
            details: domain.Details,
    ) -> domain.Results:
        """Return browse model suitable for rendering."""
        async with self._repo.transaction():
            access = await self._repo.check_access(user, item_uuid)

            if access.does_not_exist:
                raise exceptions.NotFound(f'Item {item_uuid} does not exist')

            if access.is_not_given:
                if user.is_anon():
                    raise exceptions.Unauthorized(
                        f'Anon user has no access to {item_uuid}'
                    )
                else:
                    raise exceptions.Forbidden(
                        f'User {user.uuid} ({user.name}) '
                        f'has no access to {item_uuid}'
                    )

            location = await self._repo.get_location(user,
                                                     item_uuid,
                                                     details)

            item = await self._repo.get_item(item_uuid)

            if user.is_anon():
                items = await self._repo.get_children(item_uuid, details)
                total_items = await self._repo.count_items(item_uuid)
            else:
                items = await self._repo.get_specific_children(
                    user=user,
                    item_uuid=item_uuid,
                    details=details,
                )
                total_items = await self._repo.count_specific_items(
                    user=user,
                    item_uuid=item_uuid,
                )

            result = domain.Results(
                item=item,
                total_items=total_items,
                total_pages=details.calc_total_pages(total_items),
                items=items,
                details=details,
                location=location,
            )

        return result
