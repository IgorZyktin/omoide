# -*- coding: utf-8 -*-
"""Application utility functions.
"""
import fastapi

from omoide import domain


def to_simple_items(
        request: fastapi.Request,
        items: list[domain.Item],
) -> list[dict]:
    """Convert Item objects into simple renderable form."""
    empty_href = request.url_for('static', path='empty.png')
    return [
        to_simple_item(request, item, empty_href)
        for item in items
    ]


def to_simple_item(
        request: fastapi.Request,
        item: domain.Item,
        empty_href: str,
) -> dict:
    """Convert Item object into simple renderable form."""
    if item.is_collection:
        href = request.url_for('browse', uuid=item.uuid)
    else:
        href = request.url_for('preview', uuid=item.uuid)

    if item.thumbnail_ext is None:
        thumbnail = empty_href
    else:
        thumbnail = (
            f'/content/thumbnail/{item.owner_uuid}/{item.thumbnail_path}'
        )

    return {
        'uuid': item.uuid,
        'name': item.name,
        'is_collection': item.is_collection,
        'href': href,
        'thumbnail': thumbnail,
        'number': item.number,
    }
