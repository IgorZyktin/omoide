"""Common utils.
"""
import re
from typing import Any
from typing import Pattern
from typing import Tuple
from typing import Type

from omoide.domain import errors


def assert_error(
        result: errors.Error | Any,
        error_type: Type[errors.Error] | Tuple[Type[errors.Error], ...],
        regex: str | Pattern[str] = '',
) -> errors.Error:
    """Process expected Error."""
    if not isinstance(result, errors.Error):
        actual_result_type = type(result).__name__
        msg = ('Expected to get subclass of Error, '
               f'got {actual_result_type} instead: {result!r}')
        raise TypeError(msg)

    if not isinstance(result, error_type):
        if isinstance(error_type, tuple):
            names = [x.__name__ for x in error_type]
            get_what = f'get one of types {tuple(names)}'
        else:
            get_what = f'get type {error_type.__name__}'

        actual_type = type(result).__name__
        msg = f'Expected to {get_what}, got type {actual_type}: {result}'
        raise TypeError(msg)

    if regex:
        match_expr = re.search(result.message, regex)

        if match_expr is None:
            msg = ('Regex pattern did not match.\n '
                   f'Regex: {regex!r}\n '
                   f'Input: {result.message!r}')
            raise ValueError(msg)

    return result
