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

    actions.Media.CREATE_OR_UPDATE,
    actions.Media.READ,
    actions.Media.DELETE,
))


class Policy(interfaces.AbsPolicy):
    """Policy checker."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo

    async def is_restricted(
            self,
            user: domain.User,
            uuid: UUID,
            action: actions.Action,
    ) -> Optional[errors.Error]:
        """Return Error if action is not permitted."""
        error = None

        if action in ITEM_RELATED:
            access = await self.items_repo.check_access(user, uuid)

            if access.does_not_exist:
                error = errors.ItemDoesNotExist(uuid=uuid)

            elif access.is_not_given or access.is_not_owner:
                error = errors.ItemRequiresAccess(uuid=uuid)

        else:
            error = errors.UnexpectedAction(action=action.name)

        return error or None
