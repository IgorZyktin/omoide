# -*- coding: utf-8 -*-
"""Access policy.
"""
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain import actions
from omoide.domain import errors
from omoide.domain import interfaces

ITEM_RELATED = frozenset((
    actions.EXIF.CREATE_OR_UPDATE,
    actions.EXIF.READ,
    actions.EXIF.DELETE,

    actions.Media.CREATE,
    actions.Media.READ,
    actions.Media.DELETE,

    actions.Metainfo.READ,
    actions.Metainfo.UPDATE,
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

        if action in ITEM_RELATED and uuid is not None:
            access = await self.items_repo.check_access(user, uuid)

            if access.does_not_exist:
                error = errors.ItemDoesNotExist(uuid=uuid)

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
            if user.is_anon():
                error = errors.ItemModificationByAnon()

            elif access.is_not_given or access.is_not_owner:
                error = errors.ItemRequiresAccess(uuid=uuid)

        else:
            assert action is actions.Item.READ
            if access.is_not_given:
                error = errors.ItemRequiresAccess(uuid=uuid)

        return error or None
