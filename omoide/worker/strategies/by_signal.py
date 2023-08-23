"""Begin operations by signal."""
import signal
import threading

from omoide.worker import interfaces


class SignalStrategy(interfaces.AbsStrategy):
    """Begin operations by signal."""

    def __init__(
            self,
            delay: float,
    ) -> None:
        """Initialize instance."""
        self._delay = delay
        self._event = threading.Event()
        self._stopping = False
        self._double_set = False

    def start(self) -> None:
        """Prepare for work."""
        signal.signal(signal.SIGHUP, self._handle)

    def stop(self) -> None:
        """Prepare to exit."""
        self._stopping = True

    def wait(self) -> bool:
        """Block until got command, return True for stop."""
        if self._double_set:
            self._double_set = False
            self._event.clear()
            return self._stopping

        self._double_set = False
        self._event.wait()
        self._event.clear()
        return self._stopping

    def adjust(self, done_something: bool) -> None:
        """Adjust behaviour according to result."""

    def _handle(self, signum: int, frame) -> None:
        """Block until got command."""
        _ = signum
        _ = frame
        if self._event.is_set():
            self._double_set = True
        else:
            self._event.set()
