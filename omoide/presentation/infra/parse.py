# -*- coding: utf-8 -*-
"""Request attributes extraction.
"""
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

    return common.Details(
        page=max(1, page),
        items_per_page=items_per_page,
        items_per_page_async=items_per_page_async,
    )
