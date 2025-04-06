"""Common utils."""

from collections.abc import Collection
from collections.abc import Iterable
from collections.abc import Iterator
import datetime
from itertools import zip_longest
import re
from typing import Any
from typing import TypeVar
from uuid import UUID


def get_bucket(uuid: UUID | str, length: int = 2) -> str:
    """Get bucket name from uuid.

    >>> get_bucket('92b0fa01-72a3-4300-9bb7-5a440da37f93')
    '92'
    """
    if isinstance(uuid, str):
        return str(UUID(uuid))[:length]
    return str(uuid)[:length]


def group_to_size(iterable: Iterable, group_size: int = 2, default: Any = '?') -> Iterator[tuple]:
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


def serialize_model(model: Any, do_not_serialize: Collection[str] = frozenset()) -> str:
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


def to_simple_type(something: Any) -> Any:  # noqa: PLR0911 Too many return statements
    """Convert one item."""
    if something is None:
        return None

    if something is True or something is False:
        return something

    if isinstance(something, datetime.datetime):
        return something.isoformat()

    if isinstance(something, list):
        return [to_simple_type(value) for value in something]

    if isinstance(something, set):
        return [to_simple_type(value) for value in something]

    if isinstance(something, dict):
        return {key: to_simple_type(value) for key, value in something.items()}

    return str(something)


def serialize(payload: dict[str, Any]) -> dict[str, str | None]:
    """Convert dictionary to a web-compatible format."""
    return {str(key): to_simple_type(value) for key, value in payload.items()}


TAGS_PATTERN = re.compile(r'(\s+\+\s+|\s+-\s+)')


def parse_tags(query: str) -> tuple[set[str], set[str]]:
    """Split  user query into tags."""
    tags_include: set[str] = set()
    tags_exclude: set[str] = set()

    parts = TAGS_PATTERN.split(query)
    clean_parts = [x.strip() for x in parts if x.strip()]

    if not clean_parts:
        return tags_include, tags_exclude

    if clean_parts[0] not in ('+', '-'):
        clean_parts.insert(0, '+')

    for operator, tag in group_to_size(clean_parts):
        _tag = str(tag).lower()
        if operator == '+':
            tags_include.add(_tag)
        else:
            tags_exclude.add(_tag)

    return tags_include, tags_exclude
