"""Common utils.
"""
import re
from typing import Tuple
from typing import Type
from typing import Pattern

from omoide.domain import errors
from omoide.infra.special_types import E
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Success
from omoide.infra.special_types import V


def resolve_error(
        result: Failure[E] | Success[V],
        error_type: Type[errors.Error] | Tuple[Type[errors.Error], ...],
        regex: str | Pattern[str] = '',
) -> E:
    """Process expected Failure."""
    if not isinstance(result, Failure):
        actual_result_type = type(result).__name__
        msg = ('Expected to get Failure, '
               f'got {actual_result_type} instead: {result}')
        raise TypeError(msg)

    if not isinstance(result.error, error_type):
        if isinstance(error_type, tuple):
            names = [x.__name__ for x in error_type]
            get_what = f'get one of types {tuple(names)}'
        else:
            get_what = f'get type {error_type.__name__}'

        actual_type = type(result.error).__name__
        msg = f'Expected to {get_what}, got type {actual_type}: {result.error}'
        raise TypeError(msg)

    if regex:
        match_expr = re.search(result.error.message, regex)

        if match_expr is None:
            msg = ('Regex pattern did not match.\n '
                   f'Regex: {regex!r}\n '
                   f'Input: {result.error.message!r}')
            raise ValueError(msg)

    return result.error


def resolve_success(result: Failure[E] | Success[V]) -> V:
    """Process expected Success."""
    if not isinstance(result, Success):
        actual_result_type = type(result).__name__
        msg = ('Expected to get Success, '
               f'got {actual_result_type} instead: {result}')
        raise TypeError(msg)
    return result.value
