"""Begin operations by timer."""
from omoide.daemons.worker import interfaces


class TimerStrategy(interfaces.AbsStrategy):
    """Begin operations by timer."""

    def __init__(
            self,
            min_interval: float,
            max_interval: float,
            warm_up_coefficient: float,
    ) -> None:
        """Initialize instance."""
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.warm_up_coefficient = warm_up_coefficient

    def adjust_interval(self, operations: int) -> float:
        """Change interval based on amount of operations done."""
        # if operations:
        #     self.sleep_interval = self.config.min_interval
        # else:
        #     self.sleep_interval = min((
        #         self.sleep_interval * self.config.warm_up_coefficient,
        #         self.config.max_interval,
        #     ))
        # return self.sleep_interval