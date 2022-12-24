# -*- coding: utf-8 -*-
"""Application utility functions.
"""
import fastapi

from omoide import domain
from omoide.presentation import web
from omoide.presentation.dependencies import get_templates


def to_simple_items(
        request: fastapi.Request,
        prefix_size: int,
        items: list[domain.Item],
) -> list[dict]:
    """Convert Item objects into simple renderable form."""
    templates = get_templates()
    https_url_for = templates.env.globals['https_url_for']
    empty_href = https_url_for(request, 'static', path='empty.png')
    return [
        to_simple_item(request, prefix_size, item, empty_href)
        for item in items
    ]


def to_simple_item(
        request: fastapi.Request,
        prefix_size: int,
        item: domain.Item,
        empty_href: str,
) -> dict:
    """Convert Item object into simple renderable form."""
    if item.is_collection:
        href = request.url_for('app_browse', uuid=item.uuid)
    else:
        href = request.url_for('app_preview', uuid=item.uuid)

    if item.thumbnail_ext is None:
        thumbnail = empty_href
    else:
        locator = web.Locator(
            request=request,
            prefix_size=prefix_size,
            item=item,
        )
        thumbnail = locator.thumbnail

    return {
        'uuid': item.uuid,
        'name': item.name,
        'is_collection': item.is_collection,
        'href': href,
        'thumbnail': thumbnail,
        'number': item.number,
    }
