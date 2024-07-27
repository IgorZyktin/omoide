"""Use cases for Media-related operations."""
from omoide import models
from omoide.infra import custom_logging
from omoide.omoide_api.common.use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


class DeleteProcessedMediaUseCase(BaseAPIUseCase):
    """Use case for cleaning processed records."""

    async def execute(self, user: models.User) -> None:
        """Execute."""
        self.ensure_not_anon(user, operation='delete media data')

        async with self.mediator.storage.transaction():
            LOG.info('User {} is deleting processed media', user)

            if user.is_admin:
                await self.mediator.media_repo.delete_all_processed_media()
            else:
                await self.mediator.media_repo.delete_processed_media(user)
