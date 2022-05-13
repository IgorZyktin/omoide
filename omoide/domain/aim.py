# -*- coding: utf-8 -*-
"""Object that describes user's desired output.

Contains all parameters about pagination, ordering etc.
"""
from pydantic import BaseModel

__all__ = [
    'Aim',
    'aim_from_params',
]


class Aim(BaseModel):
    """Object that describes user's desired output."""
    ordered: bool
    nested: bool
    last_seen: int

    @property
    def random(self) -> bool:
        """Return True if items must be returned in random order."""
        return not self.ordered

    @property
    def flat(self) -> bool:
        """Return True if items must be returned only from the first layer."""
        return not self.nested


def aim_from_params(params: dict) -> Aim:
    """Parse original string from request."""
    raw_ordered = params.get('ordered')
    if raw_ordered is None:
        ordered = False
    else:
        ordered = raw_ordered == 'on'

    raw_nested = params.get('nested')
    if raw_nested is None:
        nested = False
    else:
        nested = raw_nested == 'on'

    raw_last_seen = params.get('last_seen')
    try:
        last_seen = int(raw_last_seen)
    except (ValueError, TypeError):
        last_seen = -1

    return Aim(
        ordered=ordered,
        nested=nested,
        last_seen=last_seen,
    )
