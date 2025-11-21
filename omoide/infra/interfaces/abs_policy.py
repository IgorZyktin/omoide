"""Special class that checks permissions."""

import abc

from omoide import models


class AbsPolicy(abc.ABC):
    """Special class that checks permissions."""

    @staticmethod
    @abc.abstractmethod
    def ensure_registered(user: models.User, to: str, error_message: str | None = None) -> None:
        """Raise if user is anon."""

    @staticmethod
    @abc.abstractmethod
    def ensure_owner(
        user: models.User,
        item: models.Item,
        to: str,
        error_message: str | None = None,
    ) -> None:
        """Raise if one user tries to modify object of some other user."""
