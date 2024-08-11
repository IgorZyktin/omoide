"""All possible user actions."""
import enum


class Action(enum.Enum):
    """Base action type."""


# noinspection PyArgumentList
class Media(Action):
    """Operations on Media."""
    CREATE = enum.auto()


# noinspection PyArgumentList
class Item(Action):
    """Operations on Item."""
    CREATE = enum.auto()
    READ = enum.auto()
    UPDATE = enum.auto()
    DELETE = enum.auto()
