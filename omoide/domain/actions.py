# -*- coding: utf-8 -*-
"""All possible actions.
"""
import enum


class Action(enum.Enum):
    """Base action type."""


# noinspection PyArgumentList
class EXIF(Action):
    """Operations on EXIF."""
    CREATE_OR_UPDATE = enum.auto()
    READ = enum.auto()
    DELETE = enum.auto()


# noinspection PyArgumentList
class Media(Action):
    """Operations on Media."""
    CREATE = enum.auto()
    READ = enum.auto()
    DELETE = enum.auto()


# noinspection PyArgumentList
class Item(Action):
    """Operations on Item."""
    CREATE = enum.auto()
    READ = enum.auto()
    UPDATE = enum.auto()
    DELETE = enum.auto()


# noinspection PyArgumentList
class Metainfo(Action):
    """Operations on Metainfo."""
    READ = enum.auto()
    UPDATE = enum.auto()
