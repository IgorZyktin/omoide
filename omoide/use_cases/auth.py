# -*- coding: utf-8 -*-
"""Use case for auth.
"""
from fastapi.security import HTTPBasicCredentials

from omoide.domain import auth
from omoide.domain import interfaces


class AuthUseCase:
    """Use case for auth."""

    def __init__(self, repo: interfaces.AbsRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            credentials: HTTPBasicCredentials,
            authenticator: interfaces.AbsAuthenticator,
    ) -> auth.User:
        """Return user model."""
        user = await self._repo.get_user_by_login(credentials.username)

        if user is None:
            return auth.User.new_anon()

        if authenticator.password_is_correct(
                given_password=credentials.password.encode(),
                reference=user.password.encode(),
        ):
            return user

        return auth.User.new_anon()
