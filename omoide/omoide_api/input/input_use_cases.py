"""Use cases that process commands from users."""

from omoide import const
from omoide import models
from omoide.omoide_api.common.use_cases import BaseAPIUseCase


class AutocompleteUseCase(BaseAPIUseCase):
    """Use case for suggesting tag autocomplete."""

    async def execute(
        self,
        user: models.User,
        tag: str,
    ) -> list[str]:
        """Execute."""
        if len(tag) < const.MINIMAL_AUTOCOMPLETE_SIZE:
            return []

        async with self.mediator.storage.transaction():
            if user.is_anon:
                variants = await self.mediator.search_repo \
                    .autocomplete_tag_anon(
                        tag=tag,
                        limit=const.AUTOCOMPLETE_VARIANTS,
                    )
            else:
                variants = await self.mediator.search_repo \
                    .autocomplete_tag_known(
                        user=user,
                        tag=tag,
                        limit=const.AUTOCOMPLETE_VARIANTS,
                    )

        return variants
