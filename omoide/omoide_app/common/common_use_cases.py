"""Common use case elements."""

from omoide.infra.mediator import Mediator


class BaseAPPUseCase:
    """Base use case class for APP."""

    def __init__(self, mediator: Mediator) -> None:
        """Initialize instance."""
        self.mediator = mediator
