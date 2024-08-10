"""Access policy.
"""
from typing import Optional
from uuid import UUID

from omoide import interfaces
from omoide import models
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import exceptions

ITEM_RELATED = frozenset((
    actions.Media.CREATE,
))

READ_ONLY = frozenset((
    actions.Item.READ,
))


class Policy(interfaces.AbsPolicy):
    """Policy checker."""

    async def is_restricted(
        self,
        user: models.User,
        uuid: UUID | None,
        action: actions.Action,
    ) -> errors.Error | None:
        """Return Error if action is not permitted."""
        error: Optional[errors.Error] = None

        if isinstance(action, actions.Item) or uuid is None:
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
        user: models.User,
        uuid: UUID,
        action: actions.Action,
    ) -> errors.Error | None:
        """Check specifically for item related actions."""
        error: Optional[errors.Error] = None

        access = await self.items_repo.check_access(user, uuid)

        if access.does_not_exist:
            return errors.ItemDoesNotExist(uuid=uuid)

        if action in (actions.Item.CREATE,
                      actions.Item.UPDATE,
                      actions.Item.DELETE):
            # on create we're using uuid of the parent, not the item itself
            if user.is_anon:
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
        user: models.User,
        uuid: UUID,
        action: actions.Action,
    ) -> None:
        """Raise if action is not permitted."""
        access = await self.items_repo.check_access(user, uuid)

        if isinstance(action, actions.Item):
            self._check_item_related(uuid, access)
            self._check_for_item(uuid, access)
            return

        if action in ITEM_RELATED and uuid is not None:
            self._check_item_related(uuid, access)
            return

        raise exceptions.UnexpectedActionError(action=action)

    @staticmethod
    def _check_for_item(
        item_uuid: UUID,
        access: models.AccessStatus,
    ) -> None:
        """Raise if action is not permitted."""
        if access.is_not_owner:
            raise exceptions.CannotModifyItemError(item_uuid=item_uuid)

    @staticmethod
    def _check_item_related(
        item_uuid: UUID,
        access: models.AccessStatus,
    ) -> None:
        """Raise if action is not permitted."""
        if access.is_not_given:
            raise exceptions.ItemRequiresAccessError(item_uuid=item_uuid)

        if access.does_not_exist:
            raise exceptions.ItemDoesNotExistError(item_uuid=item_uuid)
