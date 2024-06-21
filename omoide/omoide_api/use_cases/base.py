"""Base use case class for API.
"""
import abc

from omoide.infra.mediator import Mediator


class BaseAPIUseCase(abc.ABC):
    """Base use case class for API."""

    def __init__(self, mediator: Mediator) -> None:
        """Initialize instance."""
        self.mediator = mediator
