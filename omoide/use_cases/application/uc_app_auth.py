# -*- coding: utf-8 -*-
"""Use case for authentication.
"""
from fastapi.security import HTTPBasicCredentials

import omoide.domain.models
from omoide import domain
from omoide.domain import interfaces

__all__ = [
    'AuthUseCase',
]

from omoide.domain.interfaces.in_infra import in_authenticator

from omoide.domain.interfaces.in_storage.in_repositories import \
    in_rp_users_read


class AuthUseCase:
    """Use case for authentication."""

    def __init__(self, users_repo: in_rp_users_read.AbsUsersReadRepository) -> None:
        """Initialize instance."""
        self.users_repo = users_repo

    async def execute(
            self,
            credentials: HTTPBasicCredentials,
            authenticator: in_authenticator.AbsAuthenticator,
    ) -> omoide.domain.models.User:
        """Return user model."""
        user = await self.users_repo.read_user_by_login(credentials.username)

        if user is None:
            return omoide.domain.models.User.new_anon()

        if authenticator.password_is_correct(
                given_password=credentials.password,
                reference=user.password,
        ):
            return user

        return omoide.domain.models.User.new_anon()
