# -*- coding: utf-8 -*-
"""Interface for access policy.
"""
import abc
from typing import Optional
from uuid import UUID

from omoide import domain
from omoide.domain import actions
from omoide.domain.errors import Error


class AbsPolicy(abc.ABC):
    """Abstract policy checker."""

    @abc.abstractmethod
    async def is_restricted(
            self,
            user: domain.User,
            uuid: UUID,
            action: actions.Action,
    ) -> Optional[Error]:
        """Return Error if action is not permitted."""
