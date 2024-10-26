"""Repository that performs operations on items."""

from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Connection

from omoide import exceptions
from omoide import models
from omoide.database import db_models
from omoide.database.interfaces.abs_items_repo import AbsItemsRepo


class ItemsRepo(AbsItemsRepo[Connection]):
    """Repository that performs operations on items."""

    @staticmethod
    def _item_from_response(response: Any) -> models.Item:
        """Convert DB response to item model."""
        return models.Item(
            id=response.id,
            uuid=response.uuid,
            parent_uuid=response.parent_uuid,
            owner_uuid=response.owner_uuid,
            name=response.name,
            number=response.number,
            is_collection=response.is_collection,
            content_ext=response.content_ext,
            preview_ext=response.preview_ext,
            thumbnail_ext=response.thumbnail_ext,
            tags=response.tags,
            permissions={UUID(x) for x in response.permissions},
        )

    def get_by_id(
        self,
        conn: Connection,
        item_id: int,
    ) -> models.Item:
        """Return Item with given id."""
        stmt = sa.select(db_models.Item).where(db_models.Item.id == item_id)
        response = conn.execute(stmt).first()

        if response is None:
            msg = 'Item with ID {item_id} does not exist'
            raise exceptions.DoesNotExistError(msg, user_id=item_id)

        return self._item_from_response(response)

    def get_by_uuid(
        self,
        conn: Connection,
        uuid: UUID,
    ) -> models.Item:
        """Return User with given UUID."""
        stmt = sa.select(db_models.Item).where(db_models.Item.uuid == uuid)
        response = conn.execute(stmt).first()

        if response is None:
            msg = 'Item with UUID {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=uuid)

        return self._item_from_response(response)

    def get_children(
        self,
        conn: Connection,
        item: models.Item,
    ) -> list[models.Item]:
        """Return children of given item."""
        stmt = (
            sa.select(db_models.Item)
            .where(db_models.Item.parent_uuid == item.uuid)
            .order_by(db_models.Item.id)
        )
        response = conn.execute(stmt).fetchall()
        return [self._item_from_response(x) for x in response]

    def get_parents(
        self,
        conn: Connection,
        item: models.Item,
    ) -> list[models.Item]:
        """Return parents of given item."""
        parents: list[models.Item] = []
        parent_uuid = item.parent_uuid

        while parent_uuid:
            stmt = sa.select(db_models.Item).where(
                db_models.Item.uuid == parent_uuid
            )
            raw_parent = conn.execute(stmt).fetchone()

            if raw_parent is None:
                break

            parent = self._item_from_response(raw_parent)
            parents.append(parent)
            parent_uuid = parent.parent_uuid

        return list(reversed(parents))

    def save(self, conn: Connection, item: models.Item) -> None:
        """Save given item."""
        stmt = (
            sa.update(db_models.Item)
            .values(
                parent_uuid=item.parent_uuid,
                name=item.name,
                status=item.status.value,
                number=item.number,
                is_collection=item.is_collection,
                content_ext=item.content_ext,
                preview_ext=item.preview_ext,
                thumbnail_ext=item.thumbnail_ext,
                tags=tuple(item.tags),
                permissions=tuple(str(x) for x in item.permissions),
            )
            .where(
                db_models.Item.id == item.id,
            )
        )
        conn.execute(stmt)
