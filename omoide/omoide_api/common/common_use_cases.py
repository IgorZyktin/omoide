"""Common use case elements."""

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
        conn,
        user: models.User,
        uuid: UUID | None,
        parent_uuid: UUID | None,
        owner_uuid: UUID | None,
        name: str,
        number: int | None,
        is_collection: bool,
        tags: set[str],
        permissions: set[UUID],
    ) -> models.Item:
        """Create single item."""
        if uuid is None:
            valid_uuid = uuid4()
        else:
            valid_uuid = uuid

        msg = 'You are not allowed to create items for other users'

        if owner_uuid is not None and owner_uuid != user.uuid:
            raise exceptions.NotAllowedError(msg)

        if parent_uuid is None:
            parent = await self.mediator.users.get_root_item(conn, user)
        else:
            parent = await self.mediator.items.get_by_uuid(conn, parent_uuid)
            if parent.owner_uuid != user.uuid:
                raise exceptions.NotAllowedError(msg)

        item = models.Item(
            id=-1,
            uuid=valid_uuid,
            parent_uuid=parent.uuid,
            owner_uuid=parent.owner_uuid,
            name=name,
            number=number or -1,
            is_collection=is_collection,
            content_ext=None,
            preview_ext=None,
            thumbnail_ext=None,
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

        await self.mediator.items.create(conn, item)
        await self.mediator.meta.create(conn, metainfo)

        return item

    async def post_item_creation(
        self,
        conn,
        item: models.Item,
        parent_computed_tags: dict[UUID, set[str]],
    ) -> tuple[set[models.User], set[str]]:
        """Update computed values after operation."""
        affected_users: list[models.User] = []

        if item.permissions:
            affected_users = await self.mediator.users.select(conn, uuids=item.permissions)

        computed_tags = await self.mediator.misc.update_computed_tags(
            item=item,
            parent_computed_tags=parent_computed_tags.get(item.uuid, set()),
        )

        return set(affected_users), computed_tags
