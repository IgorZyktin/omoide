"""Check thumbnails."""

import base64
from collections.abc import Iterator
from typing import Any
import urllib.parse
import urllib.request
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Connection
from sqlalchemy import Engine

from omoide import models
from omoide.database import db_models


def fix_missing_thumbnails(
    engine: Engine,
    site_url: str,
    create: bool,
    marker: int,
    limit: int,
    user: str,
    password: str,
) -> None:
    """Create signatures for items that miss them."""
    with engine.begin() as conn:
        for id_, _, item_uuid, _ in _get_items_without_thumbnails(conn, marker, limit):
            string = f'Missing: item_id={id_}, {site_url}/preview/{item_uuid}'
            if create:
                child_with_thumbnail = _get_child_with_thumbnail(conn, id_)
                if child_with_thumbnail is not None:
                    _, child_uuid = child_with_thumbnail
                    _copy_thumbnail_for_item(site_url, child_uuid, item_uuid, user, password)
                    string += ' [Fixed]'

            print(string)  # noqa: T201


def _get_items_without_thumbnails(conn: Connection, marker: int, limit: int) -> Iterator[Any]:
    """Get info from DB."""
    query = (
        sa.select(
            db_models.Item.id,
            db_models.User.uuid,
            db_models.Item.uuid,
            db_models.Item.name,
        )
        .join(
            db_models.User,
            db_models.User.id == db_models.Item.owner_id,
            isouter=True,
        )
        .where(
            db_models.Item.status == models.Status.AVAILABLE,
            db_models.Item.thumbnail_ext == sa.null(),
            db_models.Item.id > marker,
        )
        .order_by(db_models.Item.id)
        .limit(limit)
    )

    response = conn.execute(query).all()
    yield from response


def _get_child_with_thumbnail(conn: Connection, parent_id: int) -> tuple[int, UUID] | None:
    """Get info from DB."""
    query = """
        WITH RECURSIVE nested_items AS
               (SELECT items.id            AS id,
                       items.number        AS number,
                       items.uuid          AS uuid,
                       items.parent_id     AS parent_id,
                       items.thumbnail_ext AS thumbnail_ext
                 FROM items
                WHERE items.parent_id = :parent_id
                UNION
                SELECT items.id            AS id,
                       items.number        AS number,
                       items.uuid          AS uuid,
                       items.parent_id     AS parent_id,
                       items.thumbnail_ext AS thumbnail_ext
                FROM items
                         INNER JOIN nested_items
                                    ON items.parent_id = nested_items.id)
        SELECT nested_items.id,
               nested_items.number,
               nested_items.uuid,
               nested_items.thumbnail_ext,
               i2.id as parent_id
        FROM nested_items
        LEFT JOIN items i2 ON nested_items.parent_id = i2.id
        ORDER BY number
        """
    response = conn.execute(sa.text(query), {'parent_id': parent_id}).all()
    for row in response:
        if row.thumbnail_ext is not None:
            return row.id, row.uuid

    return None


def _copy_thumbnail_for_item(
    site_url: str,
    child_uuid: UUID,
    parent_uuid: UUID,
    user: str,
    password: str,
) -> None:
    """Create new task."""
    auth_str = f'{user}:{password}'
    encoded_auth = base64.b64encode(auth_str.encode('ascii')).decode('ascii')

    req = urllib.request.Request(  # noqa: S310
        f'{site_url}/api/v1/actions/copy_image/{child_uuid}/to/{parent_uuid}',  # noqa: S310
        method='POST',  # noqa: S310
    )  # noqa: S310
    req.add_header('Authorization', f'Basic {encoded_auth}')
    req.add_header('Content-Type', 'application/json')

    with urllib.request.urlopen(req) as response:  # noqa: S310
        _ = response.read().decode('utf-8')
