"""Use cases for heavy operations."""
import abc
import asyncio
import time
from typing import Any
from uuid import UUID

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide import utils
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase

LOG = custom_logging.get_logger(__name__)


class BaseRebuildTagsUseCase(BaseAPIUseCase, abc.ABC):
    """Base class for tag rebuilds."""
    affected_target: str

    @abc.abstractmethod
    async def _execute(
        self,
        user: models.User,
        target_user: models.User | None,
        job_id: int,
        *args: bool,
    ) -> int:
        """Execute."""

    async def execute(
        self,
        user: models.User,
        target: models.User | models.Item | None,
        job_id: int,
        *args: bool,
    ) -> None:
        """Execute."""
        start = time.perf_counter()
        total = 0

        # TODO - make separate methods finish_long_job and fail_long_job
        # TODO - calculate time inside _execute

        try:
            loop = asyncio.get_running_loop()
            coro = await loop.run_in_executor(None, self._execute, user,
                                              target, job_id, *args)
            total = await coro
        except Exception as exc:
            duration = time.perf_counter() - start
            LOG.exception(
                'Failed to complete background rebuilding of {}, '
                'command by {}, target is {}, job_id is {} ({} changes)',
                self.affected_target,
                user,
                target,
                job_id,
                total,
            )
            await self.mediator.misc_repo.finish_long_job(
                id=job_id,
                status='fail',
                duration=duration,
                operations=0,
                error=f'{type(exc).__name__}: {exc}',
            )
        else:
            duration = time.perf_counter() - start
            LOG.info(
                'Done background rebuilding of {}, '
                'command by {}, target is {}, job_id is {} ({} changes in {})',
                self.affected_target,
                user,
                target or 'anon',
                job_id,
                total,
                duration,
            )
            await self.mediator.misc_repo.finish_long_job(
                id=job_id,
                status='done',
                duration=duration,
                operations=total,
                error='',
            )


class RebuildKnownTagsUseCase(BaseRebuildTagsUseCase):
    """Use case for rebuilding known tags."""
    affected_target = 'known tags'

    async def pre_execute(
        self,
        admin: models.User,
        target: UUID | None,
    ) -> tuple[models.User | None, int]:
        """Prepare for execution."""
        self.ensure_admin(admin, subject=self.affected_target)
        extras: dict[str, Any] = {}

        async with self.mediator.storage.transaction():
            if target is None:
                LOG.info(
                    'User {} is rebuilding {} for anon user',
                    admin,
                    self.affected_target,
                )
                target_user = None
                user_uuid = None
                extras.update({'target_user_uuid': None})

            else:
                target_user = await self.mediator.users_repo.get_user(target)
                LOG.info(
                    'User {} is rebuilding {} for user {}',
                    admin,
                    self.affected_target,
                    target_user,
                )
                user_uuid = target_user.uuid
                extras.update({'target_user_uuid': str(target_user.uuid)})

            job_id = await self.mediator.misc_repo.start_long_job(
                name='rebuilding-of-known-tags',
                user_uuid=user_uuid or admin.uuid,
                target_uuid=None,
                added=[],
                deleted=[],
                started=utils.now(),
                extras=extras,
            )

        return target_user, job_id

    async def _execute(
        self,
        user: models.User,
        target_user: models.User | None,
        job_id: int,
        *args: bool,
    ) -> int:
        """Execute."""
        repo = self.mediator.misc_repo

        async with self.mediator.storage.transaction():
            if target_user is None:
                LOG.info(
                    'Known tags rebuilding for '
                    'anon has started (command by {})',
                    user,
                )
                known_tags = await repo.calculate_known_tags_anon(
                    batch_size=const.DB_BATCH_SIZE,
                )
            else:
                LOG.info(
                    'Known tags rebuilding for '
                    '{} has started (command by {})',
                    target_user,
                    user,
                )
                known_tags = await repo.calculate_known_tags_known(
                    user=target_user,
                    batch_size=const.DB_BATCH_SIZE,
                )

        async with self.mediator.storage.transaction():
            if target_user is None:
                await repo.drop_known_tags_anon()
                await repo.insert_known_tags_anon(known_tags)
                LOG.info(
                    'Known tags rebuilding for '
                    'anon has finished (command by {})',
                    user,
                )
            else:
                await repo.drop_known_tags_known(target_user)
                await repo.insert_known_tags_known(target_user, known_tags)
                LOG.info(
                    'Known tags rebuilding for '
                    '{} has finished (command by {})',
                    target_user,
                    user,
                )

        return len(known_tags)


class RebuildComputedTagsUseCase(BaseRebuildTagsUseCase):
    """Use case for rebuilding computed tags."""
    affected_target = 'computed tags'

    async def pre_execute(
        self,
        admin: models.User,
        user_uuid: UUID,
    ) -> tuple[models.User, models.Item, int]:
        """Prepare for execution."""
        self.ensure_admin(admin, subject=self.affected_target)

        async with self.mediator.storage.transaction():
            owner = await self.mediator.users_repo.get_user(user_uuid)
            item = await self.mediator.items_repo.get_root_item(owner)

            LOG.info(
                'User {} is rebuilding {} for item {} (owner is {})',
                admin,
                self.affected_target,
                item,
                owner,
            )

            job_id = await self.mediator.misc_repo.start_long_job(
                name='rebuilding-of-computed-tags',
                user_uuid=admin.uuid,
                target_uuid=item.uuid,
                added=[],
                deleted=[],
                started=utils.now(),
                extras={'target_user_uuid': str(user_uuid)},
            )

        return owner, item, job_id

    async def _compute_tags_for_one_item(
        self,
        item: models.Item,
        parent_tags: set[str],
        total: int,
        including_children: bool,
    ) -> int:
        """Compute tags for given item."""
        total += 1
        computed_tags = item.get_computed_tags(parent_tags)

        async with self.mediator.storage.transaction():
            await self.mediator.misc_repo.replace_computed_tags(item,
                                                                computed_tags)
            if including_children:
                children = await self.mediator.items_repo.get_children(item)

                for child in children:
                    child_tags = child.get_computed_tags(computed_tags)
                    await self.mediator.misc_repo.replace_computed_tags(
                        child, computed_tags)
                    total = await self._compute_tags_for_one_item(
                        child, child_tags, total, including_children)

        return total

    async def _execute(
        self,
        user: models.User,
        item: models.Item,
        job_id: int,
        *args: bool,
    ) -> int:
        """Execute."""
        LOG.info(
            'Recompute of tags for {} has started (command by {})',
            item,
            user,
        )

        total = await self._compute_tags_for_one_item(
            item,
            set(),
            0,
            *args,
        )

        LOG.info(
            'Recompute of tags for {} has finished '
            '(command by {})',
            item,
            user,
        )

        return total


class CopyImageUseCase(BaseAPIUseCase):
    """Copy image from one item to another."""

    async def execute(
        self,
        user: models.User,
        source_uuid: UUID,
        target_uuid: UUID,
    ) -> list[const.MEDIA_TYPE]:
        """Execute."""
        self.ensure_not_anon(user, operation='copy image for item')

        async with self.mediator.storage.transaction():
            source = await self.mediator.items_repo.get_item(source_uuid)
            target = await self.mediator.items_repo.get_item(target_uuid)

            self.ensure_admin_or_owner(user, source, subject='item images')
            self.ensure_admin_or_owner(user, target, subject='item images')

            media_types = await self.mediator.object_storage.copy_all_objects(
                source_item=source,
                target_item=target,
            )

            if media_types:
                await self.mediator.meta_repo.update_metainfo_extras(
                    item_uuid=target_uuid,
                    new_extras={'copied_image_from': str(source_uuid)},
                )

        return media_types
