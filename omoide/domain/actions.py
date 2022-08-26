# -*- coding: utf-8 -*-
"""All possible actions.
"""
import enum


class Action(enum.Enum):
    """Base action type."""


class EXIF(Action):
    """Operations on EXIF."""
    CREATE_OR_UPDATE = enum.auto()
    READ = enum.auto()
    DELETE = enum.auto()


class Media(Action):
    """Operations on Media."""
    CREATE_OR_UPDATE = enum.auto()
    READ = enum.auto()
    DELETE = enum.auto()
