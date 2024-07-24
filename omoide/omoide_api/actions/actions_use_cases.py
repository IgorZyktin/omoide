"""Use cases for heavy operations."""
import asyncio
import time
from uuid import UUID

from omoide import models
from omoide import utils
from omoide.infra import custom_logging
from omoide.omoide_api.common.use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


class RebuildKnownTagsUseCase(BaseAPIUseCase):
    """Use case for rebuilding known tags for anon."""

    async def pre_execute(
        self,
        admin: models.User,
        target: UUID | None,
    ) -> tuple[models.User, int]:
        """Prepare for execution."""
        async with self.mediator.storage.transaction():
            if target is None:
                self.ensure_admin(admin, subject='known tags for anon')
                LOG.info(
                    'User {} is rebuilding known tags for anon user',
                    admin,
                )
                name = 'known-tags-anon'
                target_user = None
                extras = {}

            else:
                target_user = await self.mediator.users_repo.get_user(target)
                self.ensure_admin_or_owner(admin, target_user,
                                           'known tags for a user')
                name = 'known-tags-user'
                LOG.info(
                    'User {} is rebuilding known tags for user',
                    admin,
                    target_user,
                )
                extras = {'target_user_uuid': target_user.uuid}

            new_job = await self.mediator.misc_repo.start_long_job(
                name=name,
                user_uuid=admin.uuid if target is None else target_user.uuid,
                target_uuid=None,
                added=[],
                deleted=[],
                status='started',
                started=utils.now(),
                extras=extras,
            )

        return target_user, new_job

    async def execute(
        self,
        user: models.User,
        target_user: models.User | None,
        job_id: int,
    ) -> None:
        """Execute."""
        start = time.perf_counter()

        try:
            total = await self._execute(user, target_user, job_id)
        except Exception as exc:
            LOG.exception(
                'Failed to complete background rebuilding of known tags, '
                'command by {}, target is {}, job_id is {}',
                user,
                target_user,
                job_id,
            )
            await self.mediator.misc_repo.finish_long_job(
                id=job_id,
                status='fail',
                duration=time.perf_counter() - start,
                operations=0,
                error=f'{type(exc).__name__}: {exc}',
            )
        else:
            LOG.info(
                'Done background rebuilding of known tags, '
                'command by {}, target is {}, job_id is {}',
                user,
                target_user,
                job_id,
            )
            await self.mediator.misc_repo.finish_long_job(
                id=job_id,
                status='done',
                duration=time.perf_counter() - start,
                operations=total,
                error='',
            )

    async def _execute(
        self,
        user: models.User,
        target_user: models.User,
        job_id: int,
    ) -> int:
        """Execute."""
        # TODO
        await asyncio.sleep(5)
        return 1
