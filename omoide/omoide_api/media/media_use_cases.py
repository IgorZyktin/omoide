"""Use cases for Media-related operations."""
from omoide import models
from omoide.infra import custom_logging
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


class DeleteProcessedMediaUseCase(BaseAPIUseCase):
    """Use case for cleaning processed records."""

    async def execute(self, user: models.User) -> int:
        """Execute."""
        self.ensure_not_anon(user, operation='delete media data')

        async with self.mediator.storage.transaction():
            LOG.info('User {} is deleting processed media', user)

            repo = self.mediator.media_repo

            if user.is_admin:
                total_rows_affected = await repo.delete_all_processed_media()
            else:
                total_rows_affected = await repo.delete_processed_media(user)

        return total_rows_affected
