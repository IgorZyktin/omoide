"""Use cases for heavy operations."""
import asyncio
import time
from uuid import UUID

from omoide import const
from omoide import models
from omoide import utils
from omoide.infra import custom_logging
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


class RebuildKnownTagsUseCase(BaseAPIUseCase):
    """Use case for rebuilding known tags for anon."""

    async def pre_execute(
        self,
        admin: models.User,
        target: UUID | None,
    ) -> tuple[models.User | None, int]:
        """Prepare for execution."""
        self.ensure_admin(admin, subject='known tags')

        async with self.mediator.storage.transaction():
            if target is None:
                LOG.info(
                    'User {} is rebuilding known tags for anon user',
                    admin,
                )
                name = 'known-tags-anon'
                target_user = None
                user_uuid = None
                extras = {}

            else:
                target_user = await self.mediator.users_repo.get_user(target)
                name = 'known-tags-user'
                LOG.info(
                    'User {} is rebuilding known tags for user {}',
                    admin,
                    target_user,
                )
                user_uuid = target_user.uuid
                extras = {'target_user_uuid': target_user.uuid}

            new_job = await self.mediator.misc_repo.start_long_job(
                name=name,
                user_uuid=user_uuid or admin.uuid,
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
        target_user: models.User | None,
        job_id: int,
    ) -> int:
        """Execute."""
        # TODO
        await asyncio.sleep(5)
        return 1


class CopyImageUseCase(BaseAPIUseCase):
    """Copy image from one item to another."""

    async def execute(
        self,
        user: models.User,
        source_uuid: UUID,
        target_uuid: UUID,
    ) -> list[int]:
        """Execute."""
        self.ensure_not_anon(user, operation='copy content for items')
        job_ids: list[int] = []

        async with self.mediator.storage.transaction():
            source = await self.mediator.items_repo.get_item(source_uuid)
            target = await self.mediator.items_repo.get_item(target_uuid)

            self.ensure_admin_or_owner(user, source, subject='item content')
            self.ensure_admin_or_owner(user, target, subject='item content')

            if source.content_ext is not None:
                job_id = await self.mediator.media_repo.copy_image(
                    owner_uuid=source.owner_uuid,
                    source_uuid=source_uuid,
                    target_uuid=target_uuid,
                    media_type=const.CONTENT,
                    ext=source.content_ext,
                )
                job_ids.append(job_id)

            if source.preview_ext is not None:
                job_id = await self.mediator.media_repo.copy_image(
                    owner_uuid=source.owner_uuid,
                    source_uuid=source_uuid,
                    target_uuid=target_uuid,
                    media_type=const.PREVIEW,
                    ext=source.preview_ext,
                )
                job_ids.append(job_id)

            if source.thumbnail_ext is not None:
                job_id = await self.mediator.media_repo.copy_image(
                    owner_uuid=source.owner_uuid,
                    source_uuid=source_uuid,
                    target_uuid=target_uuid,
                    media_type=const.THUMBNAIL,
                    ext=source.thumbnail_ext,
                )
                job_ids.append(job_id)

            if job_ids:
                await self.mediator.meta_repo.update_metainfo_extras(
                    uuid=target_uuid,
                    new_extras={'copied_image_from': str(source_uuid)},
                )

        return job_ids
