"""Use cases for auth-related APP operations."""
from omoide import models
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase


class LoginUserUseCase(BaseAPIUseCase):
    """Login user on the site."""

    async def execute(
        self,
        login: str,
        password: str,
    ) -> models.User:
        """Execute."""
        async with self.mediator.storage.transaction():
            users = await self.mediator.users_repo.get_users(
                login=login,
                limit=1,
            )

            if not users:
                return models.User.new_anon()

            user = users[0]

            if self.mediator.authenticator.password_is_correct(
                given_password=password,
                reference=user.password.get_secret_value(),
            ):
                return user

        return models.User.new_anon()
