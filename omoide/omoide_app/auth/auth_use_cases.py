"""Use cases for auth-related APP operations."""

from omoide import models
from omoide import utils
from omoide.omoide_api.common.common_use_cases import BaseAPIUseCase


class LoginUserUseCase(BaseAPIUseCase):
    """Login user on the site."""

    async def execute(self, login: str, password: str) -> models.User:
        """Execute."""
        async with self.mediator.database.transaction() as conn:
            response = await self.mediator.users.get_by_login(conn, login)

            if not response:
                return models.User.new_anon()

            user, reference_password, auth_complexity = response

            if self.mediator.authenticator.password_is_correct(
                given_password=password,
                reference=reference_password,
                auth_complexity=auth_complexity,
            ):
                user.last_login = utils.now()
                await self.mediator.users.save(conn, user)
                return user

        return models.User.new_anon()
