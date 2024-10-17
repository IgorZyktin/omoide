"""Implementation for display commands."""

from typing import Any
from uuid import UUID

import colorama
import sqlalchemy as sa
from sqlalchemy.orm import Session

from omoide.omoide_cli.display import code_du
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


def du(
    only_users: list[UUID] | None,
    db_url: str,
    threshold: float = 0.1,
) -> None:
    """Show disk usage by users."""
    engine = sa.create_engine(db_url, pool_pre_ping=True, future=True)

    with Session(engine) as session:
        users = code_du.get_all_corresponding_users(session, only_users)

    with engine.begin() as conn:
        stats: list[code_du.Stats] = []
        for user in users:
            new_stats = code_du.scan_for_user(conn, user)
            stats.append(new_stats)

    code_du.print_results(stats, threshold)
