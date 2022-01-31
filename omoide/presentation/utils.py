# -*- coding: utf-8 -*-
"""Application utility functions.
"""


def sep_digits(number: int | float | str, precision: int = 2) -> str:
    """Return number as string with separated thousands.

    >>> sep_digits('12345678')
    '12345678'
    >>> sep_digits(12345678)
    '12 345 678'
    >>> sep_digits(1234.5678)
    '1 234.57'
    >>> sep_digits(1234.5678, precision=4)
    '1 234.5678'
    """
    if isinstance(number, int):
        result = '{:,}'.format(number).replace(',', ' ')

    elif isinstance(number, float):
        if precision == 0:
            int_value = int(round(number, precision))
            result = '{:,}'.format(int_value).replace(',', ' ')

        else:
            float_value = round(number, precision)
            result = '{:,}'.format(float_value).replace(',', ' ')

        if '.' in result:
            tail = result.rsplit('.', maxsplit=1)[-1]
            result += '0' * (precision - len(tail))

    else:
        result = str(number)

    return result


def make_search_report(total: int, duration: float) -> str:
    """Format human-readable search report."""
    total_str = sep_digits(total)
    return f'Found {total_str} items in {duration:0.3f} sec.'
