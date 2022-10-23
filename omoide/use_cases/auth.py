# -*- coding: utf-8 -*-
"""Use case for auth.
"""
from uuid import UUID

from fastapi.security import HTTPBasicCredentials

from omoide.domain import interfaces, auth


class AuthUseCase:
    """Use case for auth."""

    def __init__(self, repo: interfaces.AbsRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            credentials: HTTPBasicCredentials,
            authenticator: interfaces.AbsAuthenticator,
            env: str,
            test_users: frozenset[UUID],
    ) -> auth.User:
        """Return user model."""
        user = await self._repo.get_user_by_login(credentials.username)

        if user is None:
            return auth.User.new_anon()

        if env == 'prod' and user.uuid in test_users:
            return auth.User.new_anon()

        if authenticator.password_is_correct(credentials.password.encode(),
                                             user.password.encode()):
            return user

        return auth.User.new_anon()
