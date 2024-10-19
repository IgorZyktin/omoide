"""Use cases for heavy operations."""

import abc
import asyncio
import time
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
            coro = await loop.run_in_executor(
                None, self._execute, user, target, job_id, *args
            )
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


class RebuildKnownTagsAnonUseCase(BaseAPIUseCase):
    """Use case for rebuilding known tags for anon."""

    async def execute(self, admin: models.User) -> int:
        """Initiate serial operation execution."""
        self.ensure_admin(admin, subject='known tags for anon')

        async with self.mediator.storage.transaction():
            LOG.info(
                'User {} requested rebuilding of known tags for anon user',
                admin,
            )
            repo = self.mediator.misc_repo
            operation_id = await repo.create_serial_operation(
                name=const.SERIAL_REBUILD_KNOWN_TAGS_ANON,
            )

        return operation_id


class RebuildKnownTagsUserUseCase(BaseAPIUseCase):
    """Use case for rebuilding known tags for known user."""

    async def execute(self, admin: models.User, user_uuid: UUID) -> int:
        """Initiate serial operation execution."""
        self.ensure_admin(admin, subject=f'known tags for user {user_uuid}')

        async with self.mediator.storage.transaction():
            user = await self.mediator.users_repo.get_user_by_uuid(user_uuid)
            LOG.info(
                'User {} requested rebuilding of known tags for user {}',
                admin,
                user,
            )
            repo = self.mediator.misc_repo
            operation_id = await repo.create_serial_operation(
                name=const.SERIAL_REBUILD_KNOWN_TAGS_USER,
                extras={'user_uuid': str(user_uuid)},
            )

        return operation_id


class RebuildKnownTagsAllUseCase(BaseAPIUseCase):
    """Use case for rebuilding known tags for all registered users."""

    async def execute(self, admin: models.User) -> int:
        """Initiate serial operation execution."""
        self.ensure_admin(admin,
                          subject=f'known tags for all registered users')

        async with self.mediator.storage.transaction():
            LOG.info(
                'User {} requested rebuilding of '
                'known tags for all registered users',
                admin,
            )
            repo = self.mediator.misc_repo
            operation_id = await repo.create_serial_operation(
                name=const.SERIAL_REBUILD_KNOWN_TAGS_ALL,
                extras={},
            )

        return operation_id


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
            owner = await self.mediator.users_repo.get_user_by_uuid(user_uuid)
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
        parents: dict[UUID, models.ParentTags],
        total: int,
        including_children: bool,
    ) -> int:
        """Compute tags for given item."""
        total += 1

        async with self.mediator.storage.transaction():
            if (
                item.parent_uuid is not None
                and item.parent_uuid not in parents
            ):
                parent = await self.mediator.items_repo.get_item(
                    uuid=item.parent_uuid,
                )

                tags = await self.mediator.misc_repo.get_computed_tags(parent)

                parents[parent.uuid] = models.ParentTags(
                    parent=parent,
                    computed_tags=tags,
                )

            parent_entry = parents.get(item.parent_uuid)
            parent_tags = parent_entry.computed_tags if parent_entry else set()
            new_tags = await self.mediator.misc_repo.update_computed_tags(
                item=item,
                parent_computed_tags=parent_tags,
            )

            parents[item.uuid] = models.ParentTags(
                parent=item,
                computed_tags=new_tags,
            )

            if including_children:
                children = await self.mediator.items_repo.get_children(item)

                for child in children:
                    total = await self._compute_tags_for_one_item(
                        item=child,
                        parents=parents,
                        total=total,
                        including_children=including_children,
                    )

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

        parents: dict[UUID, models.ParentTags] = {}

        if item.parent_uuid is not None:
            parent = await self.mediator.items_repo.get_item(item.parent_uuid)
            tags = await self.mediator.misc_repo.get_computed_tags(parent)
            parents[parent.uuid] = models.ParentTags(
                parent=parent,
                computed_tags=tags,
            )

        total = await self._compute_tags_for_one_item(
            item,
            parents,
            0,
            *args,
        )

        LOG.info(
            'Recompute of tags for {} has finished ' '(command by {})',
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
