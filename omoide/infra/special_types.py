# -*- coding: utf-8 -*-
"""Custom types used to tie the infrastructure together.
"""
from typing import Generic
from typing import TypeVar

V = TypeVar('V', covariant=True)
E = TypeVar('E', covariant=True)


class Success(Generic[V]):
    """Abstract container that holds result of execution."""

    def __init__(self, value: V):
        """Initialize instance."""
        self.value = value


class Failure(Generic[E]):
    """Abstract container that holds description why something failed."""

    def __init__(self, error: E):
        """Initialize instance."""
        self.error = error


Result = Failure[E] | Success[V]
