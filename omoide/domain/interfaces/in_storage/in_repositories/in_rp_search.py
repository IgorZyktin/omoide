"""Repository that performs all search queries."""
import abc

from omoide import domain
from omoide import models
from omoide.domain.interfaces.in_storage.in_repositories import in_rp_base


class AbsSearchRepository(in_rp_base.AbsBaseRepository):
    """Repository that performs all search queries."""

    @abc.abstractmethod
    async def count_matching_items(
            self,
            user: models.User,
            aim: domain.Aim,
    ) -> int:
        """Count matching items for search query."""

    @abc.abstractmethod
    async def get_matching_items(
            self,
            user: models.User,
            aim: domain.Aim,
            obligation: domain.Obligation,
    ) -> list[domain.Item]:
        """Return matching items for search query."""

    @abc.abstractmethod
    async def autocomplete_tag_anon(
            self,
            tag: str,
            limit: int,
    ) -> list[str]:
        """Autocomplete tag for anon user."""

    @abc.abstractmethod
    async def autocomplete_tag_known(
            self,
            user: models.User,
            tag: str,
            limit: int,
    ) -> list[str]:
        """Autocomplete tag for known user."""

    @abc.abstractmethod
    async def count_all_tags(
            self,
            user: models.User,
    ) -> list[tuple[str, int]]:
        """Return statistics for used tags."""

    @abc.abstractmethod
    async def count_all_tags_anon(self) -> dict[str, int]:
        """Return statistics for used tags."""
