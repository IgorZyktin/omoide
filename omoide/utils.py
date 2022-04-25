# -*- coding: utf-8 -*-
"""Common utils.
"""
import datetime


def now() -> datetime.datetime:
    """Return current moment in time with timezone."""
    return datetime.datetime.now(tz=datetime.timezone.utc)
