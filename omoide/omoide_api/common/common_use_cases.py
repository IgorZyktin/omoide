"""Common use case elements."""

import abc
from uuid import UUID

from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide import utils
from omoide.infra.mediator import Mediator

LOG = custom_logging.get_logger(__name__)


class BaseAPIUseCase(abc.ABC):
    """Base use case class for API."""

    def __init__(self, mediator: Mediator) -> None:
        """Initialize instance."""
        self.mediator = mediator

    @staticmethod
    def ensure_not_anon(
        user: models.User,
        operation: str = '',
        error_message: str = '',
    ) -> None:
        """Raise if Anon requesting this."""
        if user.is_not_anon:
            return

        if error_message:
            msg = error_message
        elif operation:
            msg = f'Anonymous users are not allowed to {operation}'
        else:
            msg = (
                'Anonymous users are not allowed to perform such requests'
            )

        raise exceptions.AccessDeniedError(msg)

    @staticmethod
    def ensure_admin_or_owner_or_allowed_to(
        user: models.User,
        item: models.Item,
        subject: str = '',
        error_message: str = '',
    ) -> None:
        """Raise if one user tries to manage object of some other user."""
        if any(
            (
                user.is_admin,
                item.owner_uuid == user.uuid,
                str(user.uuid) in item.permissions,
            )
        ):
            return

        if error_message:
            msg = error_message
        elif subject:
            msg = (
                'You are not allowed to perform '
                f'such operations with {subject}'
            )
        else:
            msg = 'You are not allowed to perform such operations'

        raise exceptions.AccessDeniedError(msg)

    @staticmethod
    def ensure_admin_or_owner(
        user: models.User,
        target: models.Item | models.User,
        subject: str = '',
        error_message: str = '',
    ) -> None:
        """Raise if one user tries to manage object of some other user."""
        conditions: list[bool] = []

        if isinstance(target, models.User):
            conditions.append(user.uuid == target.uuid)
        else:
            conditions.append(target.owner_uuid == user.uuid)

        if all(conditions) or user.is_admin:
            return

        if error_message:
            msg = error_message
        elif subject:
            msg = (
                'You are not allowed to perform '
                f'such operations with {subject}'
            )
        else:
            msg = 'You are not allowed to perform this operation'

        raise exceptions.AccessDeniedError(msg)

    @staticmethod
    def ensure_admin_or_allowed_to(
        user: models.User,
        item: models.Item,
        subject: str = '',
        error_message: str = '',
    ) -> None:
        """Raise if one user tries to manage object of some other user."""
        if all(
            (
                item.owner_uuid == user.uuid,
                str(user.uuid) in item.permissions
            )
        ) or user.is_admin:
            return

        if error_message:
            msg = error_message
        elif subject:
            msg = (
                'You are not allowed to perform '
                f'such operations with {subject}'
            )
        else:
            msg = 'You are not allowed to perform such operations'

        raise exceptions.AccessDeniedError(msg)

    @staticmethod
    def ensure_admin(
        user: models.User,
        subject: str = '',
        error_message: str = '',
    ) -> None:
        """Raise if user is not admin."""
        if user.is_admin:
            return

        if error_message:
            msg = error_message
        elif subject:
            msg = (
                'You are not allowed to perform '
                f'such operations with {subject}'
            )
        else:
            msg = 'You are not allowed to perform such operations'

        raise exceptions.AccessDeniedError(msg)


class BaseItemUseCase(BaseAPIUseCase):
    """Base class for use cases that create items."""

    async def create_one_item(
        self,
        user: models.User,
        uuid: UUID | None,
        parent_uuid: UUID | None,
        owner_uuid: UUID | None,
        name: str,
        number: int | None,
        is_collection: bool,
        tags: list[str],
        permissions: list[UUID],
        content_ext: str | None = None,
        preview_ext: str | None = None,
        thumbnail_ext: str | None = None,
    ) -> models.Item:
        """Create single item."""
        if uuid is None:
            valid_uuid = await self.mediator.items_repo.get_free_uuid()
        else:
            valid_uuid = uuid

        msg = 'You are not allowed to create items for other users'

        if owner_uuid is not None and owner_uuid != user.uuid:
            raise exceptions.NotAllowedError(msg)

        if parent_uuid is None:
            parent = await self.mediator.items_repo.get_root_item(user)
            owner_uuid = parent.owner_uuid

        else:
            parent = await self.mediator.items_repo.get_item(parent_uuid)
            if parent.owner_uuid != user.uuid:
                raise exceptions.NotAllowedError(msg)
            owner_uuid = parent.owner_uuid

        item = models.Item(
            id=-1,
            uuid=valid_uuid,
            parent_uuid=parent.uuid,
            owner_uuid=owner_uuid,
            name=name,
            number=number or -1,
            is_collection=is_collection,
            content_ext=content_ext,
            preview_ext=preview_ext,
            thumbnail_ext=thumbnail_ext,
            tags=tags,
            permissions=permissions,
        )

        metainfo = models.Metainfo(
            item_uuid=item.uuid,
            created_at=utils.now(),
            updated_at=utils.now(),
            deleted_at=None,
            user_time=None,
            content_type=None,
            extras={},
            content_size=None,
            preview_size=None,
            thumbnail_size=None,
            content_width=None,
            content_height=None,
            preview_width=None,
            preview_height=None,
            thumbnail_width=None,
            thumbnail_height=None,
        )

        comp_tags = await self.mediator.misc_repo.update_computed_tags(item)
        repo = self.mediator.misc_repo

        if item.permissions:
            affected_users = await self.mediator.users_repo.get_users(
                uuids=item.permissions,
            )
            for affected_user in affected_users:
                await repo.increment_known_tags_for_known_user(
                    user=affected_user,
                    tags=comp_tags,
                )

        await self.mediator.items_repo.create_item(item)
        await self.mediator.meta_repo.create_metainfo(metainfo)

        return item

    async def delete_one_item(self, item: models.Item) -> None:
        """Delete item with all corresponding media."""
        children = await self.mediator.items_repo.get_children(item)

        for child in children:
            await self.delete_one_item(child)

        await self.mediator.object_storage.delete_all_objects(item)
        LOG.warning('Deleting item {}', item)
        await self.mediator.items_repo.delete_item(item)
