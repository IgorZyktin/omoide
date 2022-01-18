# -*- coding: utf-8 -*-
"""User query parser.
"""
import re
from itertools import zip_longest
from typing import Iterable, Any, Iterator

from pydantic import BaseModel
from starlette.datastructures import QueryParams

from omoide.domain import search


class ExtQuery(BaseModel):
    """Extended query, also includes some app-specific stuff."""
    raw_query: str
    query: search.Query
    folded: bool

    def as_str(self) -> str:
        """Convert to urlsafe string."""
        string = (
            f'?q={self.raw_query}'
            f'&page={self.query.page}'
            f'&folded={self.folded}'
        )

        string = string.replace(' ', '%20')
        string = string.replace(',', '%2C')
        string = string.replace('+', '%2B')

        return string

    def at_page(self, page: int) -> 'ExtQuery':
        """Return new query for given page."""
        return type(self)(
            raw_query=self.raw_query,
            query=search.Query(
                tags_include=self.query.tags_include,
                tags_exclude=self.query.tags_exclude,
                page=page,
            ),
            folded=self.folded,
        )


def from_request(params: QueryParams) -> ExtQuery:
    """Create new query from request params."""
    raw_query = params.get('q', '')
    tags_include, tags_exclude = parse_tags(raw_query)
    folded = str(params.get('folded', '')).lower() == 'true'

    try:
        page = int(params.get('page', 1))
    except (ValueError, TypeError):
        page = 1

    return ExtQuery(
        raw_query=raw_query,
        query=search.Query(
            tags_include=tags_include,
            tags_exclude=tags_exclude,
            page=page,
        ),
        folded=folded,
    )


def from_form(query: ExtQuery, additional_query: str) -> ExtQuery:
    """Populate existing query with form contents."""
    tags_include, tags_exclude = parse_tags(additional_query)
    return ExtQuery(
        raw_query=additional_query,
        query=search.Query(
            tags_include=tags_include,
            tags_exclude=tags_exclude,
            page=query.query.page,
        ),
        folded=query.folded,
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
