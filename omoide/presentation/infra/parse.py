# -*- coding: utf-8 -*-
"""Request attributes extraction.
"""
from typing import Optional
from uuid import UUID

from starlette.datastructures import QueryParams

from omoide.domain import common


def details_from_params(
        params: QueryParams,
        items_per_page: int,
        items_per_page_async: int = -1,
) -> common.Details:
    """Create details from request params."""
    try:
        page = int(params.get('page', 1))
    except (ValueError, TypeError):
        page = 1

    try:
        anchor = int(params.get('anchor', 1))
    except (ValueError, TypeError):
        anchor = -1

    return common.Details(
        page=max(1, page),
        anchor=anchor,
        items_per_page=items_per_page,
        items_per_page_async=items_per_page_async,
    )


def cast_uuid(uuid: str) -> Optional[UUID]:
    """Try casting given string as uuid."""
    try:
        result = UUID(uuid)
    except (ValueError, AttributeError):
        result = None
    return result


def cast_int(number: str) -> Optional[int]:
    """Try casting given string as int."""
    try:
        result = int(number)
    except ValueError:
        result = None
    return result
