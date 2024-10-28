"""The most abstract level of all database-related entities."""
import abc
from typing import Generic
from typing import TypeVar

ConnectionT = TypeVar('ConnectionT')


class AbsRepo(Generic[ConnectionT], abc.ABC):
    """Abstract base repo."""
