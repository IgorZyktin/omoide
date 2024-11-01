"""Common use case elements."""

from typing import Any
from uuid import UUID
from uuid import uuid4

from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide import utils
from omoide.infra.mediator import Mediator

LOG = custom_logging.get_logger(__name__)


class BaseAPIUseCase:
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
            msg = 'Anonymous users are not allowed to perform such requests'

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
                user.uuid in item.permissions,
            )
        ):
            return

        if error_message:
            msg = error_message
        elif subject:
            msg = 'You are not allowed to perform ' f'such operations with {subject}'
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
            msg = 'You are not allowed to perform ' f'such operations with {subject}'
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
        if (
            all(
                (
                    item.owner_uuid == user.uuid,
                    user.uuid in item.permissions,
                )
            )
            or user.is_admin
        ):
            return

        if error_message:
            msg = error_message
        elif subject:
            msg = 'You are not allowed to perform ' f'such operations with {subject}'
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
            msg = 'You are not allowed to perform ' f'such operations with {subject}'
        else:
            msg = 'You are not allowed to perform such operations'

        raise exceptions.AccessDeniedError(msg)


class BaseItemUseCase(BaseAPIUseCase):
    """Base class for use cases that create items."""

    async def create_one_item(
        self,
        conn: Any,  # TODO - find a way to skip this argument
        user: models.User,
        uuid: UUID | None,
        parent_uuid: UUID | None,
        name: str,
        number: int | None,
        is_collection: bool,
        tags: list[str],
        permissions: list[dict[str, UUID | str]],
    ) -> models.Item:
        """Create single item."""
        if uuid is None:
            valid_uuid = uuid4()
        else:
            valid_uuid = uuid

        msg = 'You are not allowed to create items for other users'

        if parent_uuid is None:
            parent = await self.mediator.users.get_root_item(conn, user)
        else:
            parent = await self.mediator.items.get_by_uuid(conn, parent_uuid)
            if parent.owner_uuid != user.uuid:
                raise exceptions.NotAllowedError(msg)

        _permissions: set[int] = set()
        for human_readable_user in permissions:
            user_uuid = human_readable_user.get('uuid')
            if not isinstance(user_uuid, UUID):
                continue
            user = await self.mediator.users.get_by_uuid(conn, user_uuid)
            _permissions.add(user.id)

        item = models.Item(
            id=-1,
            uuid=valid_uuid,
            parent_id=parent.id,
            parent_uuid=parent.uuid,
            owner_id=parent.owner_id,
            owner_uuid=parent.owner_uuid,
            name=name,
            status=models.Status.CREATED,
            number=number or -1,
            is_collection=is_collection,
            content_ext=None,
            preview_ext=None,
            thumbnail_ext=None,
            tags=set(tags),
            permissions=_permissions,
            extras={},
        )

        item_id = await self.mediator.items.create(conn, item)

        metainfo = models.Metainfo(
            item_id=item_id,
            created_at=utils.now(),
            updated_at=utils.now(),
            deleted_at=None,
            user_time=None,
            content_type=None,
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

        await self.mediator.meta.create(conn, metainfo)

        return item
