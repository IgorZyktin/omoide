"""Common utils."""

from collections.abc import Callable
from collections.abc import Collection
from collections.abc import Iterable
from collections.abc import Iterator
import datetime
import functools
from itertools import zip_longest
import re
import sys
from typing import Any
from typing import TypeVar
from uuid import UUID


def now() -> datetime.datetime:
    """Return current moment in time with timezone."""
    return datetime.datetime.now(tz=datetime.timezone.utc)


def get_bucket(uuid: UUID | str, length: int = 2) -> str:
    """Get bucket name from uuid.

    >>> get_bucket('92b0fa01-72a3-4300-9bb7-5a440da37f93')
    '92'
    """
    if isinstance(uuid, str):
        return str(UUID(uuid))[:length]
    return str(uuid)[:length]


UUID_TEMPLATE = re.compile(
    '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
)


def is_valid_uuid(uuid: UUID | str) -> bool:
    """Return True if given object can be considered as UUID."""
    if isinstance(uuid, UUID):
        return True
    return UUID_TEMPLATE.match(uuid) is not None


def sep_digits(number: float | str, precision: int = 2) -> str:
    """Return number as a string with separated thousands.

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
        result = f'{number:,}'.replace(',', ' ')

    elif isinstance(number, float):
        if precision == 0:
            int_value = int(round(number, precision))
            result = f'{int_value:,}'.replace(',', ' ')

        else:
            float_value = round(number, precision)
            result = f'{float_value:,}'.replace(',', ' ')

        if '.' in result:
            tail = result.rsplit('.', maxsplit=1)[-1]
            result += '0' * (precision - len(tail))

    else:
        result = str(number)

    return result


SUFFIXES = {
    'RU': {
        'B': 'Б',
        'kB': 'кБ',
        'MB': 'МБ',
        'GB': 'ГБ',
        'TB': 'ТБ',
        'PB': 'ПБ',
        'EB': 'ЭБ',
        'KiB': 'КиБ',
        'MiB': 'МиБ',
        'GiB': 'ГиБ',
        'TiB': 'ТиБ',
        'PiB': 'ПиБ',
        'EiB': 'ЭиБ',
    },
    'EN': {
        'B': 'B',
        'kB': 'kB',
        'MB': 'MB',
        'GB': 'GB',
        'TB': 'TB',
        'PB': 'PB',
        'EB': 'EB',
        'KiB': 'KiB',
        'MiB': 'MiB',
        'GiB': 'GiB',
        'TiB': 'TiB',
        'PiB': 'PiB',
        'EiB': 'EiB',
    },
}


def human_readable_size(total_bytes: float, language: str = 'EN') -> str:
    """Convert amount of bytes into human-readable format.

    >>> human_readable_size(1023)
    '1023 B'
    """
    total_bytes = int(total_bytes)

    prefix = ''
    if total_bytes < 0:
        prefix = '-'
        total_bytes = abs(total_bytes)

    if total_bytes < 1024:  # noqa: PLR2004
        suffix = SUFFIXES[language]['B']
        return f'{prefix}{int(total_bytes)} {suffix}'

    total_bytes /= 1024  # noqa: PLR2004

    if total_bytes < 1024:  # noqa: PLR2004
        suffix = SUFFIXES[language]['KiB']
        return f'{prefix}{total_bytes:0.1f} {suffix}'

    total_bytes /= 1024  # noqa: PLR2004

    if total_bytes < 1024:  # noqa: PLR2004
        suffix = SUFFIXES[language]['MiB']
        return f'{prefix}{total_bytes:0.1f} {suffix}'

    total_bytes /= 1024  # noqa: PLR2004

    if total_bytes < 1024:  # noqa: PLR2004
        suffix = SUFFIXES[language]['GiB']
        return f'{prefix}{total_bytes:0.1f} {suffix}'

    total_bytes /= 1024  # noqa: PLR2004

    if total_bytes < 1024:  # noqa: PLR2004
        suffix = SUFFIXES[language]['TiB']
        return f'{prefix}{total_bytes:0.1f} {suffix}'

    suffix = SUFFIXES[language]['EiB']
    return f'{total_bytes / 1024 / 1024 :0.1f} {suffix}'


def human_readable_time(seconds: int) -> str:
    """Format interval as human readable description.

    >>> human_readable_time(46551387)
    '76w 6d 18h 56m 27s'
    >>> human_readable_time(600)
    '10m'
    """
    if seconds < 1:
        return '0s'

    _weeks = 0
    _days = 0
    _hours = 0
    _minutes = 0
    _seconds = 0
    _suffixes = ('w', 'd', 'h', 'm', 's')

    if seconds > 0:
        _minutes, _seconds = divmod(seconds, 60)
        _hours, _minutes = divmod(_minutes, 60)
        _days, _hours = divmod(_hours, 24)
        _weeks, _days = divmod(_days, 7)

    values = [_weeks, _days, _hours, _minutes, _seconds]
    string = ' '.join(f'{x}{_suffixes[i]}' for i, x in enumerate(values) if x)

    return string


def group_to_size(
    iterable: Iterable, group_size: int = 2, default: Any = '?'
) -> Iterator[tuple]:
    """Return contents of the iterable grouped in blocks of given size.

    >>> list(group_to_size([1, 2, 3, 4, 5, 6, 7], 2, '?'))
    [(1, 2), (3, 4), (5, 6), (7, '?')]
    >>> list(group_to_size([1, 2, 3, 4, 5, 6, 7], 3, '?'))
    [(1, 2, 3), (4, 5, 6), (7, '?', '?')]
    """
    return zip_longest(*[iter(iterable)] * group_size, fillvalue=default)


T = TypeVar('T')


def get_delta(
    before: Collection[T],
    after: Collection[T],
) -> tuple[set[T], set[T]]:
    """Return which elements were added and deleted."""
    before_set = set(before)
    after_set = set(after)
    added = after_set - before_set
    deleted = before_set - after_set
    return added, deleted


RT = TypeVar('RT')  # return type


def memorize(func: Callable[..., RT]) -> Callable[..., RT]:
    """Strict cache. Does not care about arguments.

    Can be used for functions that always return same result.
    """
    sentinel = object()
    objects: dict[str, Any] = {}

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> RT:
        """Wrap original function."""
        result = objects.get(func.__name__, sentinel)
        if result is sentinel:
            result = func(*args, **kwargs)
            objects[func.__name__] = result
        return result

    return wrapper


def serialize_model(
    model: Any, do_not_serialize: Collection[str] = frozenset()
) -> str:
    """Convert model to human-readable string."""
    attributes: list[str] = []
    model_to_list(
        model=model,
        attributes=attributes,
        do_not_serialize=do_not_serialize,
        depth=0,
    )
    return '\n'.join(attributes)


def model_to_list(
    model: Any | dict[str, Any],
    attributes: list[str],
    do_not_serialize: Collection[str],
    depth: int,
) -> None:
    """Convert each field to a list entry."""
    if isinstance(model, dict):
        payload = model
    else:
        payload = model.model_dump()

    prefix = '    ' * depth
    for key, value in payload.items():
        if isinstance(value, dict) and key not in do_not_serialize:
            line = f'{prefix}{key}:'
            attributes.append(line)
            model_to_list(value, attributes, do_not_serialize, depth + 1)
        else:
            line = f'{prefix}{key}={value!r}'
            attributes.append(line)


def split(string: str, separator: str = ',') -> list[str]:
    """Split comma separated list."""
    return [clear for raw in string.split(separator) if (clear := raw.strip())]


def get_size(obj: Any, seen: set[int] | None = None) -> int:
    """Recursively finds size of objects."""
    size = sys.getsizeof(obj)

    if seen is None:
        seen = set()

    obj_id = id(obj)

    if obj_id in seen:
        return 0

    seen.add(obj_id)

    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj])

    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)

    elif hasattr(obj, '__iter__') and not isinstance(
        obj, (str | bytes | bytearray)
    ):
        size += sum([get_size(i, seen) for i in obj])

    return size


def to_simple_type(something: Any) -> Any:
    """Convert one item."""
    if something is None:
        return None

    if something is True or something is False:
        return something

    if isinstance(something, datetime.datetime):
        return something.isoformat()

    if isinstance(something, list):
        return [to_simple_type(value) for value in something]

    return str(something)


def serialize(payload: dict[str, Any]) -> dict[str, str | None]:
    """Convert dictionary to a web-compatible format."""
    return {str(key): to_simple_type(value) for key, value in payload.items()}


def exc_to_str(exc: Exception) -> str:
    """Convert exception into readable string."""
    return f'{type(exc).__name__}: {exc}'
