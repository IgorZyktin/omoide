# -*- coding: utf-8 -*-
"""Use case for search by owner uuid.
"""
from omoide import domain
from omoide.domain import interfaces


class ByUserUseCase:
    """Use case for search by owner uuid."""

    def __init__(self, repo: interfaces.AbsByUserRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: domain.User,
            owner_uuid: str,
            details: domain.Details,
    ) -> domain.Results:
        """Return preview model suitable for rendering."""
        async with self._repo.transaction():
            if user.is_anon():
                total_items = await self._repo.count_items_of_public_user(
                    owner_uuid=owner_uuid,
                )

                items = await self._repo.get_items_of_public_user(
                    owner_uuid=owner_uuid,
                    details=details,
                )

            else:
                total_items = await self._repo.count_items_of_private_user(
                    user=user,
                    owner_uuid=owner_uuid,
                )

                items = await self._repo.get_items_of_private_user(
                    user=user,
                    owner_uuid=owner_uuid,
                    details=details,
                )

        return domain.Results(
            total_items=total_items,
            total_pages=details.calc_total_pages(total_items),
            items=items,
            details=details,
            location=None,
        )
