# -*- coding: utf-8 -*-
"""Object that describes user's desired output.

Contains all parameters about pagination, ordering etc.
"""
from pydantic import BaseModel

from omoide.presentation import constants

__all__ = [
    'Aim',
    'aim_from_params',
    'extract_int',
    'extract_bool',
]


class Aim(BaseModel):
    """Object that describes user's desired output."""
    ordered: bool
    nested: bool
    paged: bool
    last_seen: int
    items_per_page: int

    @property
    def random(self) -> bool:
        """Return True if items must be returned in random order."""
        return not self.ordered

    @property
    def flat(self) -> bool:
        """Return True if items must be returned only from the first layer."""
        return not self.nested

    def to_url(self) -> str:
        """Encode into url."""

        def _str(value: bool) -> str:
            return 'on' if value else 'off'

        return '?' + '&'.join([
            f'ordered={_str(self.ordered)}',
            f'nested={_str(self.nested)}',
            f'last_seen={self.last_seen}',
            f'items_per_page={self.items_per_page}',
        ])


def extract_bool(
        params: dict,
        key: str,
        default: bool,
) -> bool:
    """Safely extract boolean value from user input."""
    value = params.get(key)

    if value is None:
        result = default
    else:
        result = value == 'on'

    return result


def extract_int(
        params: dict,
        key: str,
        default: int,
) -> int:
    """Safely extract int value from user input."""
    try:
        result = int(params.get(key))
    except (ValueError, TypeError):
        result = default
    return result


def aim_from_params(params: dict) -> Aim:
    """Parse original string from request."""
    return Aim(
        ordered=extract_bool(params, 'ordered', False),
        nested=extract_bool(params, 'nested', False),
        paged=extract_bool(params, 'paged', False),
        last_seen=extract_int(params, 'last_seen', -1),
        items_per_page=extract_int(params, 'items_per_page',
                                   constants.ITEMS_PER_PAGE),
    )
