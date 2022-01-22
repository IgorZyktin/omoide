# -*- coding: utf-8 -*-
"""Simple duration counter.
"""
import time


class Timer:
    """Simple duration counter."""

    def __init__(self) -> None:
        """Initialize instance."""
        self.started_at = 0.0
        self.stopped_at = 0.0

    def __enter__(self) -> 'Timer':
        """Start measuring."""
        self.started_at = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop measuring."""
        self.stopped_at = time.perf_counter()

    @property
    def seconds(self) -> float:
        """Return total amount of seconds of use."""
        return self.stopped_at - self.started_at
