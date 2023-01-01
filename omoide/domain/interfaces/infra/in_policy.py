# -*- coding: utf-8 -*-
"""Interface for access policy.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain import actions
from omoide.domain.errors import Error
from omoide.domain.interfaces.in_storage \
    .in_repositories import in_rp_items_read

__all__ = [
    'AbsPolicy',
]


class AbsPolicy(abc.ABC):
    """Abstract policy checker."""

    def __init__(
            self,
            items_repo: in_rp_items_read.AbsItemsReadRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo

    @abc.abstractmethod
    async def is_restricted(
            self,
            user: domain.User,
            uuid: Optional[UUID],
            action: actions.Action,
    ) -> Optional[Error]:
        """Return Error if action is not permitted."""
