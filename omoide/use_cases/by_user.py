# -*- coding: utf-8 -*-
"""Use case for search by owner uuid.
"""
from omoide.domain import auth, by_user, search
from omoide.domain.interfaces import database


class ByUserUseCase:
    """Use case for search by owner uuid."""

    def __init__(self, repo: database.AbsByUserRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: auth.User,
            query: search.Query,
            owner_uuid: str,
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
                    limit=query.items_per_page,
                    offset=query.offset,
                )

            else:
                total_items = await self._repo.count_items_of_private_user(
                    user=user,
                    owner_uuid=owner_uuid,
                )

                items = await self._repo.get_items_of_private_user(
                    user=user,
                    owner_uuid=owner_uuid,
                    limit=query.items_per_page,
                    offset=query.offset,
                )

        total_pages = int(total_items / (query.items_per_page or 1))

        return by_user.Result(
            page=query.page,
            total_items=total_items,
            total_pages=total_pages,
            items=items,
        )
