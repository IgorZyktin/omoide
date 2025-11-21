"""Special class that checks permissions."""

import abc

from omoide import models


class AbsPolicy(abc.ABC):
    """Special class that checks permissions."""

    @staticmethod
    @abc.abstractmethod
    def ensure_registered(user: models.User, to: str, error_message: str | None = None) -> None:
        """Raise if user is anon."""
