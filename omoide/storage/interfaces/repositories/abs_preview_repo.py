"""Repository that performs all preview queries."""
import abc
from uuid import UUID

from omoide import models
from omoide.storage.interfaces.repositories.abs_browse_repo import \
    AbsBrowseRepository


class AbsPreviewRepository(AbsBrowseRepository):
    """Repository that performs all preview queries."""

    @abc.abstractmethod
    async def get_neighbours(
        self,
        user: models.User,
        uuid: UUID,
    ) -> list[UUID]:
        """Return uuids of all the neighbours for given item UUID."""
