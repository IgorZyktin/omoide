# -*- coding: utf-8 -*-
"""Use case for search by owner uuid.
"""
from omoide.domain import auth, by_user, common
from omoide.domain.interfaces import database


class ByUserUseCase:
    """Use case for search by owner uuid."""

    def __init__(self, repo: database.AbsByUserRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: auth.User,
            owner_uuid: str,
            details: common.Details,
    ) -> by_user.Result:
        """Return preview model suitable for rendering."""
        async with self._repo.transaction():
            is_public = await self._repo.user_is_public(owner_uuid)

            if is_public:
                total_items = await self._repo.count_items_of_public_user(
                    owner_uuid=owner_uuid,
                )

                items = await self._repo.get_items_of_public_user(
                    owner_uuid=owner_uuid,
                    limit=details.items_per_page,
                    offset=details.offset,
                )

            else:
                total_items = await self._repo.count_items_of_private_user(
                    user=user,
                    owner_uuid=owner_uuid,
                )

                items = await self._repo.get_items_of_private_user(
                    user=user,
                    owner_uuid=owner_uuid,
                    limit=details.items_per_page,
                    offset=details.offset,
                )

        return by_user.Result(
            page=details.page,
            total_items=total_items,
            total_pages=details.calc_total_pages(total_items),
            items=items,
        )
