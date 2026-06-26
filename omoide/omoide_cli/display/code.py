"""Implementation for display commands."""

from typing import Any
from uuid import UUID

import colorama
import sqlalchemy as sa
from sqlalchemy.orm import Session

from omoide.omoide_cli.display import code_inheritance
from omoide.omoide_cli.display import common_display

colorama.init()


def inheritance(item_uuid: UUID, db_url: str, show_uuids: bool) -> None:
    """Display all children for the item."""
    engine = sa.create_engine(db_url, pool_pre_ping=True, future=True)

    graph: dict[str, Any] = {}

    with Session(engine) as session:
        item = code_inheritance.get_item(session, item_uuid)
        code_inheritance.output_tree(
            session=session,
            item=item,
            show_uuids=show_uuids,
            graph=graph,
        )

    pretty_graph = common_display.prettify_graph(graph)
    print(pretty_graph.strip())  # noqa: T201
