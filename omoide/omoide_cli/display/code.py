"""Implementation for display commands."""

from typing import Any
from uuid import UUID

import colorama
import sqlalchemy as sa
from sqlalchemy.orm import Session

from omoide.omoide_cli.display import common_display
from omoide.storage.database import db_models

colorama.init()


def inheritance(db_url: str, item_uuid: UUID, show_uuids: bool) -> None:
    """Display all children for the item."""
    engine = sa.create_engine(db_url, pool_pre_ping=True, future=True)

    graph: dict[str, Any] = {}

    with Session(engine) as session:
        item = _get_item(session, item_uuid)
        _output_tree(
            session=session,
            item=item,
            show_uuids=show_uuids,
            graph=graph,
        )

    pretty_graph = common_display.prettify_graph(graph)
    print(pretty_graph.strip())  # noqa: T201


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


def _get_item(session: Session, item_uuid: UUID) -> db_models.Item:
    """Get item by UUID."""
    item = session.query(db_models.Item).filter_by(uuid=item_uuid).first()

    if item is None:
        msg = f'Item {item_uuid} does not exist'
        raise RuntimeError(msg)

    return item


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


def _output_tree(
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
    sub_graph = {}
    graph[key] = sub_graph

    for child in children:
        _output_tree(
            session=session,
            item=child,
            graph=sub_graph,
            show_uuids=show_uuids,
        )
