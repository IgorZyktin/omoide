"""Access policy.
"""
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import exceptions
from omoide.domain import interfaces

ITEM_RELATED = frozenset((
    actions.EXIF.CREATE,
    actions.EXIF.READ,
    actions.EXIF.UPDATE,
    actions.EXIF.DELETE,

    actions.Media.CREATE,

    actions.Metainfo.READ,
    actions.Metainfo.UPDATE,
))

READ_ONLY = frozenset((
    actions.EXIF.READ,
    actions.Metainfo.READ,
    actions.Item.READ,
))

CHANGING_ITEM_RELATED = frozenset((
    actions.EXIF.CREATE,
    actions.EXIF.UPDATE,
    actions.EXIF.DELETE,
))


class Policy(interfaces.AbsPolicy):
    """Policy checker."""

    async def is_restricted(
            self,
            user: domain.User,
            uuid: Optional[UUID],
            action: actions.Action,
    ) -> Optional[errors.Error]:
        """Return Error if action is not permitted."""
        error: Optional[errors.Error] = None

        if isinstance(action, actions.Item):
            if uuid is None:
                return errors.NoUUID(action=action.name)
            return await self._is_restricted_for_item(user, uuid, action)

        access = await self.items_repo.check_access(user, uuid)

        if action in ITEM_RELATED and uuid is not None:
            if access.does_not_exist:
                error = errors.ItemDoesNotExist(uuid=uuid)

            # TODO: rewrite it more general
            elif access.is_public and action in READ_ONLY:
                return None

            elif access.is_not_given or access.is_not_owner:
                error = errors.ItemRequiresAccess(uuid=uuid)

        else:
            error = errors.UnexpectedAction(action=action.name)

        return error or None

    async def _is_restricted_for_item(
            self,
            user: domain.User,
            uuid: UUID,
            action: actions.Item,
    ) -> Optional[errors.Error]:
        """Check specifically for item related actions."""
        error: Optional[errors.Error] = None

        access = await self.items_repo.check_access(user, uuid)

        if access.does_not_exist:
            return errors.ItemDoesNotExist(uuid=uuid)

        if action in (actions.Item.CREATE, actions.Item.UPDATE, action.DELETE):
            # on create we're using uuid of the parent, not the item itself
            if user.is_not_registered:
                error = errors.ItemModificationByAnon()

            elif access.is_not_owner:
                error = errors.ItemRequiresAccess(uuid=uuid)

        else:
            assert action is actions.Item.READ
            if access.is_not_given:
                error = errors.ItemRequiresAccess(uuid=uuid)

        return error or None

    async def check(
            self,
            user: domain.User,  # FIXME
            uuid: UUID | None,
            action: actions.Action,
    ) -> None:
        """Raise if action is not permitted."""
        access = await self.items_repo.check_access(user, uuid)

        if action in ITEM_RELATED and uuid is not None:
            self._check_item_related(uuid, action, access)
        else:
            raise exceptions.UnexpectedActionError(action=action)

    @staticmethod
    def _check_item_related(
            item_uuid: UUID,
            action: actions.Action,
            access: domain.AccessStatus,  # FIXME
    ) -> None:
        """Raise if action is not permitted."""
        if access.does_not_exist:
            raise exceptions.ItemDoesNotExistError(
                item_uuid=item_uuid,
            )

        if action in CHANGING_ITEM_RELATED and access.is_not_owner:
            raise exceptions.CannotModifyItemComponentError(
                item_uuid=item_uuid,
            )
