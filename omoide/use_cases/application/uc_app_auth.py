"""Use case for authentication."""
from fastapi.security import HTTPBasicCredentials

from omoide import models
from omoide.domain import interfaces

__all__ = [
    'AuthUseCase',
]


class AuthUseCase:
    """Use case for authentication."""

    def __init__(self, users_repo: interfaces.AbsUsersRepo) -> None:
        """Initialize instance."""
        self.users_repo = users_repo

    async def execute(
            self,
            credentials: HTTPBasicCredentials,
            authenticator: interfaces.AbsAuthenticator,
    ) -> models.User:
        """Return user model."""
        user = await self.users_repo.read_user_by_login(credentials.username)

        if user is None:
            return models.User.new_anon()

        if authenticator.password_is_correct(
                given_password=credentials.password,
                reference=user.password,
        ):
            return user

        return models.User.new_anon()
