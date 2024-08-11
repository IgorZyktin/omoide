"""Begin operations by timer."""

import time

from omoide.omoide_worker import interfaces


class TimerStrategy(interfaces.AbsStrategy):
    """Begin operations by timer."""

    def __init__(
        self,
        min_interval: float,
        max_interval: float,
        warm_up_coefficient: float,
    ) -> None:
        """Initialize instance."""
        self._min_interval = min_interval
        self._max_interval = max_interval
        self._warm_up_coefficient = warm_up_coefficient
        self._sleep_interval = min_interval
        self._stopping = False

    def init(self) -> None:
        """Prepare for work."""

    def stop(self) -> None:
        """Prepare to exit."""
        self._stopping = True

    def wait(self) -> bool:
        """Block until got command, return True for stop."""
        time.sleep(self._sleep_interval)
        return self._stopping

    def adjust(self, *, done_something: bool) -> None:
        """Adjust behaviour according to result."""
        if done_something:
            self._sleep_interval = self._min_interval
        else:
            self._sleep_interval = min(
                (
                    self._sleep_interval * self._warm_up_coefficient,
                    self._max_interval,
                )
            )
