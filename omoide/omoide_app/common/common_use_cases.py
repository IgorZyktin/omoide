"""Common use case elements."""
import abc

from omoide.infra.mediator import Mediator


class BaseAPPUseCase(abc.ABC):
    """Base use case class for APP."""

    def __init__(self, mediator: Mediator) -> None:
        """Initialize instance."""
        self.mediator = mediator
