# -*- coding: utf-8 -*-
"""Use case for auth.
"""
from fastapi.security import HTTPBasicCredentials

from omoide.domain import auth
from omoide.domain import interfaces


class AuthUseCase:
    """Use case for auth."""

    def __init__(self, users_repo: interfaces.AbsUsersRepository) -> None:
        """Initialize instance."""
        self.users_repo = users_repo

    async def execute(
            self,
            credentials: HTTPBasicCredentials,
            authenticator: interfaces.AbsAuthenticator,
    ) -> auth.User:
        """Return user model."""
        user = await self.users_repo.read_user_by_login(credentials.username)

        if user is None:
            return auth.User.new_anon()

        if authenticator.password_is_correct(
                given_password=credentials.password.encode(),
                reference=user.password.encode(),
        ):
            return user

        return auth.User.new_anon()
