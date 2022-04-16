# -*- coding: utf-8 -*-
"""User query parser.
"""
import re
from itertools import zip_longest
from typing import Iterable, Any, Iterator

from starlette.datastructures import QueryParams

from omoide.domain import common


class QueryWrapper:
    """Extended query."""

    def __init__(self, query: common.Query, details: common.Details) -> None:
        """Initialize instance."""
        self.query = query
        self.details = details

    def as_str(self) -> str:
        """Convert to urlsafe string."""
        string = (
            f'?q={self.query.raw_query}'
            f'&page={self.details.page}'
        )

        string = string.replace(' ', '%20')
        string = string.replace(',', '%2C')
        string = string.replace('+', '%2B')

        return string

    def at_page(self, page: int) -> 'QueryWrapper':
        """Return new query for given page."""
        return type(self)(
            query=self.query,
            details=self.details.at_page(page, self.details.anchor),
        )


def from_request(params: QueryParams) -> common.Query:
    """Create new query from request params."""
    raw_query = params.get('q', '')
    tags_include, tags_exclude = parse_tags(raw_query)

    return common.Query(
        raw_query=raw_query,
        tags_include=tags_include,
        tags_exclude=tags_exclude,
    )


def group_to_size(iterable: Iterable, group_size: int = 2,
                  default: Any = '?') -> Iterator[tuple]:
    """Return contents of the iterable grouped in blocks of given size.

    >>> list(group_to_size([1, 2, 3, 4, 5, 6, 7], 2, '?'))
    [(1, 2), (3, 4), (5, 6), (7, '?')]
    >>> list(group_to_size([1, 2, 3, 4, 5, 6, 7], 3, '?'))
    [(1, 2, 3), (4, 5, 6), (7, '?', '?')]
    """
    return zip_longest(*[iter(iterable)] * group_size, fillvalue=default)


PATTERN = re.compile(r'(\s\+\s|\s-\s)')


def parse_tags(raw_query: str) -> tuple[list[str], list[str]]:
    """Split  user query into tags."""
    tags_include = []
    tags_exclude = []

    parts = PATTERN.split(raw_query)
    clean_parts = [x.strip() for x in parts if x.strip()]

    if not clean_parts:
        return [], []

    if clean_parts[0] not in ('+', '-'):
        clean_parts.insert(0, '+')

    for operator, tag in group_to_size(clean_parts):
        if operator == '+':
            tags_include.append(tag)
        else:
            tags_exclude.append(tag)

    return tags_include, tags_exclude
