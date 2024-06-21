"""Use cases for User-related operations.
"""
from typing import Any

from omoide.domain.core import core_models
from omoide.omoide_api.use_cases.base import BaseAPIUseCase


class GetUsersUseCase(BaseAPIUseCase):
    """Use case for getting users."""

    async def execute(
        self,
        user: core_models.User,
    ) -> tuple[list[core_models.User], list[dict[str, Any]]]:
        """Execute."""
        users: list[core_models.User] = []
        extras: list[dict[str, Any]] = []

        if user.is_anon():
            return users, extras

        # TODO - implement business logic here

        if user.is_registered:
            return [user], [{'root_item': user.root_item}]

        return users, extras
