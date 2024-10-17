"""Code for the `inheritance` command."""

from typing import Any
from uuid import UUID

import colorama
from sqlalchemy.orm import Session

from omoide.storage.database import db_models


def get_item(session: Session, item_uuid: UUID) -> db_models.Item:
    """Get item by UUID."""
    item = session.query(db_models.Item).filter_by(uuid=item_uuid).first()

    if item is None:
        msg = f'Item {item_uuid} does not exist'
        raise RuntimeError(msg)

    return item


def output_tree(
    *,
    session: Session,
    item: db_models.Item,
    show_uuids: bool,
    graph: dict[str, Any],
) -> None:
    """Generate graph for inheritance tree."""
    if not item.is_collection:
        return

    children = _get_children(session, item)
    key = _serialize_item(item, show_uuids, len(children))
    sub_graph: dict[str, Any] = {}
    graph[key] = sub_graph

    for child in children:
        output_tree(
            session=session,
            item=child,
            graph=sub_graph,
            show_uuids=show_uuids,
        )


def _serialize_item(
    item: db_models.Item,
    show_uuids: bool,
    total_children: int,
) -> str:
    """Convert item to pretty string."""
    uuid = ''
    if show_uuids:
        uuid = (
            f'{colorama.Fore.LIGHTBLACK_EX}'
            f'<{item.uuid}>'
            f'{colorama.Fore.RESET}'
        )

    if item.parent_uuid is None:
        name = (
            f'{colorama.Fore.RED}'
            f'{item.name or "???"}'
            f'{colorama.Fore.RESET}'
        )
    else:
        name = (
            f'{colorama.Fore.GREEN}'
            f'{item.name or "???"}'
            f'{colorama.Fore.RESET}'
        )

    children = ''
    if total_children:
        children += (
            ' '
            f'{colorama.Fore.LIGHTCYAN_EX}'
            f'({total_children} children)'
            f'{colorama.Fore.RESET}'
        )

    return f'{uuid} {name}{children}'


def _get_children(
    session: Session,
    item: db_models.Item,
) -> list[db_models.Item]:
    """Get child items."""
    query = (
        session.query(db_models.Item)
        .filter_by(parent_uuid=item.uuid)
        .order_by(db_models.Item.number)
    )
    return query.all()
