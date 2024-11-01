"""Special class that checks permissions."""

import abc

from omoide import models


class AbsPolicy(abc.ABC):
    """Special class that checks permissions."""

    @staticmethod
    @abc.abstractmethod
    def ensure_registered(user: models.User, to: str, error_message: str | None = None) -> None:
        """Raise if Anon requesting this."""

    @staticmethod
    @abc.abstractmethod
    def ensure_owner(
        user: models.User,
        item: models.Item,
        to: str,
        error_message: str | None = None,
    ) -> None:
        """Raise if one user tries to modify object of some other user."""

    @staticmethod
    @abc.abstractmethod
    def ensure_represents(
        user: models.User,
        other_user: models.User,
        to: str,
        error_message: str | None = None,
    ) -> None:
        """Raise if one user tries to modify data of some other user."""

    @staticmethod
    @abc.abstractmethod
    def ensure_can_see(
        user: models.User,
        item: models.Item,
        to: str,
        error_message: str | None = None,
    ) -> None:
        """Continue execution only if user is allowed to see given item (or is admin)."""
