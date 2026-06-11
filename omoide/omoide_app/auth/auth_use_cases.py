"""Use cases for auth-related APP operations."""

import python_utilz as pu

from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.infra import interfaces as infra_interfaces


class LoginUserUseCase:
    """Login user on the site."""

    def __init__(
        self,
        authenticator: infra_interfaces.AbsAuthenticator,
        database: AbsDatabase,
        users: db_interfaces.AbsUsersRepo,
    ) -> None:
        """Initialize instance."""
        self.authenticator = authenticator
        self.database = database
        self.users = users

    async def execute(self, login: str, password: str) -> models.User:
        """Execute."""
        async with self.database.transaction() as conn:
            response = await self.users.get_by_login(conn, login)

            if not response:
                return models.User.new_anon()

            user, reference_password, auth_complexity = response

            if self.authenticator.password_is_correct(
                given_password=password,
                reference=reference_password,
                auth_complexity=auth_complexity,
            ):
                user.last_login = pu.now()
                await self.users.save(conn, user)
                return user

        return models.User.new_anon()
