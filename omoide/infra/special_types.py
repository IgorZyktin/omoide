"""Custom types used to tie the infrastructure together."""

from typing import Generic
from typing import TypeVar

V = TypeVar('V', covariant=True)
E = TypeVar('E', covariant=True)


class Success(Generic[V]):
    """Abstract container that holds result of execution."""

    def __init__(self, value: V):
        """Initialize instance."""
        self.value = value

    def __str__(self) -> str:
        """Return textual representation."""
        name = type(self).__name__
        return f'{name}(value={self.value!r})'


class Failure(Generic[E]):
    """Abstract container that holds description why something failed."""

    def __init__(self, error: E):
        """Initialize instance."""
        self.error = error

    def __str__(self) -> str:
        """Return textual representation."""
        name = type(self).__name__
        return f'{name}(error={self.error!r})'


Result = Failure[E] | Success[V]
