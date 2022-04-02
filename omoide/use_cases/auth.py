# -*- coding: utf-8 -*-
"""Use case for auth.
"""
import secrets

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
    ) -> auth.User:
        """Return user model."""
        user = await self._repo.get_user_by_login(credentials.username)

        if user is None:
            return auth.User.new_anon()

        # TODO - need to use more serious password encoding
        password_is_correct = secrets.compare_digest(
            credentials.password,
            user.password,
        )

        if password_is_correct:
            return user

        return auth.User.new_anon()
