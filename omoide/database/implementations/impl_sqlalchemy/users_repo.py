"""Repository that performs operations on users."""

from collections.abc import Collection
from uuid import UUID

import python_utilz as pu
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from omoide import exceptions
from omoide import models
from omoide.database import db_models
from omoide.database.interfaces.abs_users_repo import AbsUsersRepo


class UsersRepo(AbsUsersRepo[AsyncConnection]):
    """Repository that performs operations on users."""

    async def create(
        self,
        conn: AsyncConnection,
        user: models.User,
        encoded_password: str,
        auth_complexity: int,
    ) -> int:
        """Create new user."""
        values = {
            'uuid': user.uuid,
            'name': user.name,
            'login': user.login,
            'password': encoded_password,
            'auth_complexity': auth_complexity,
            'role': user.role,
            'is_public': user.is_public,
            'registered_at': pu.now(),
            'last_login': None,
        }

        if user.id >= 0:
            values['id'] = user.id

        stmt = sa.insert(db_models.User).values(values).returning(db_models.User.id)

        response = await conn.execute(stmt)
        user_id = int(response.scalar() or -1)
        user.id = user_id
        return user_id

    async def get_by_id(self, conn: AsyncConnection, user_id: int) -> models.User:
        """Return User with given id."""
        query = sa.select(db_models.User).where(db_models.User.id == user_id)
        response = (await conn.execute(query)).first()

        if response is None:
            msg = 'User with ID {user_id} does not exist'
            raise exceptions.DoesNotExistError(msg, user_id=user_id)

        return models.User.from_obj(response)

    async def get_by_uuid(self, conn: AsyncConnection, uuid: UUID) -> models.User:
        """Return User with given UUID."""
        query = sa.select(db_models.User).where(db_models.User.uuid == uuid)
        response = (await conn.execute(query)).first()

        if response is None:
            msg = 'User with UUID {user_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, user_uuid=uuid)

        return models.User.from_obj(response)

    async def get_by_login(
        self,
        conn: AsyncConnection,
        login: str,
    ) -> tuple[models.User, str, int] | None:
        """Return user+password for given login."""
        query = (
            sa.select(db_models.User, db_models.Item.uuid.label('root_item_uuid'))
            .join(db_models.Item, db_models.Item.owner_id == db_models.User.id)
            .where(db_models.User.login == login, db_models.Item.parent_id == sa.null())
        )

        response = (await conn.execute(query)).fetchone()

        if response is None:
            return None

        user = models.User.from_obj(response, extra_keys=['root_item_uuid'])
        return user, response.password, response.auth_complexity

    async def get_map(
        self,
        conn: AsyncConnection,
        items: Collection[models.Item],
        permissions: bool = True,
        owners: bool = False,
    ) -> dict[int, models.User | None]:
        """Get map of users for given items."""
        ids: set[int] = set()

        for item in items:
            if permissions:
                ids.update(item.permissions)
            if owners:
                ids.add(item.owner_id)

        users: dict[int, models.User | None] = dict.fromkeys(ids)
        query = sa.select(db_models.User).where(db_models.User.id.in_(ids))

        response = (await conn.execute(query)).fetchall()
        for row in response:
            user = models.User.from_obj(row)
            users[user.id] = user

        return users

    async def select(  # noqa: PLR0913 Too many arguments in function definition
        self,
        conn: AsyncConnection,
        user_id: int | None = None,
        uuid: UUID | None = None,
        login: str | None = None,
        ids: Collection[int] | None = None,
        uuids: Collection[UUID] | None = None,
        limit: int | None = None,
    ) -> list[models.User]:
        """Return filtered list of users."""
        query = sa.select(db_models.User)

        if user_id is not None:
            query = query.where(db_models.User.id == user_id)

        if uuid is not None:
            query = query.where(db_models.User.uuid == uuid)

        if login is not None:
            query = query.where(db_models.User.login == login)

        if ids is not None:
            query = query.where(db_models.User.id.in_(tuple(ids)))

        if uuids is not None:
            query = query.where(db_models.User.uuid.in_(tuple(uuids)))

        query = query.order_by(db_models.User.id)

        if limit is not None:
            query = query.limit(limit)

        response = (await conn.execute(query)).fetchall()
        return [models.User.from_obj(row) for row in response]

    async def save(self, conn: AsyncConnection, user: models.User) -> bool:
        """Save given user."""
        stmt = (
            sa.update(db_models.User)
            .values(
                name=user.name,
                login=user.login,
                role=user.role,
                is_public=user.is_public,
                registered_at=user.registered_at,
                last_login=user.last_login,
            )
            .where(db_models.User.id == user.id)
        )
        response = await conn.execute(stmt)
        return bool(response.rowcount)

    async def delete(self, conn: AsyncConnection, user: models.User) -> bool:
        """Delete given user."""
        stmt = sa.delete(db_models.User).where(db_models.User.id == user.id)
        response = await conn.execute(stmt)
        return bool(response.rowcount)

    async def get_public_user_ids(self, conn: AsyncConnection) -> set[int]:
        """Return ids of public users."""
        query = sa.select(db_models.User.id).where(db_models.User.is_public)
        response = (await conn.execute(query)).fetchall()
        return {x.id for x in response}

    async def get_root_item(self, conn: AsyncConnection, user: models.User) -> models.Item:
        """Return root item for given user."""
        query = sa.select(db_models.Item).where(
            sa.and_(
                db_models.Item.owner_id == user.id,
                db_models.Item.parent_id == sa.null(),
            )
        )

        response = (await conn.execute(query)).fetchone()

        if response is None:
            msg = 'User {user_uuid} has no root item'
            raise exceptions.DoesNotExistError(msg, user_uuid=user.uuid)

        return models.Item.from_obj(response)

    async def get_root_items_map(
        self,
        conn: AsyncConnection,
        *users: models.User,
    ) -> dict[int, models.Item | None]:
        """Return map of root items."""
        root_items: dict[int, models.Item | None] = {}

        query = sa.select(db_models.Item).where(db_models.Item.parent_uuid == sa.null())
        if users:
            ids = [user.id for user in users]
            root_items = dict.fromkeys(ids)
            query = query.where(db_models.Item.owner_id.in_(ids))

        response = (await conn.execute(query)).fetchall()
        for row in response:
            item = models.Item.from_obj(row)
            root_items[item.owner_id] = item

        return root_items

    async def calc_total_space_used_by(
        self,
        conn: AsyncConnection,
        user: models.User,
    ) -> models.SpaceUsage:
        """Return total amount of used space for user."""
        query = (
            sa.select(
                sa.func.sum(db_models.Metainfo.content_size).label('content_size'),
                sa.func.sum(db_models.Metainfo.preview_size).label('preview_size'),
                sa.func.sum(db_models.Metainfo.thumbnail_size).label('thumbnail_size'),
            )
            .join(
                db_models.Item,
                db_models.Item.id == db_models.Metainfo.item_id,
            )
            .where(db_models.Item.owner_id == user.id)
        )

        response = (await conn.execute(query)).fetchone()

        return models.SpaceUsage(
            uuid=user.uuid,
            content_size=response.content_size if response else 0,
            preview_size=response.preview_size if response else 0,
            thumbnail_size=response.thumbnail_size if response else 0,
        )

    async def count_items_by_owner(
        self,
        conn: AsyncConnection,
        user: models.User,
        collections: bool = False,
    ) -> int:
        """Return total amount of items for given user uuid."""
        query = (
            sa.select(sa.func.count().label('total_items'))
            .select_from(db_models.Item)
            .where(db_models.Item.owner_uuid == user.uuid)
        )

        if collections:
            query = query.where(db_models.Item.is_collection)

        response = (await conn.execute(query)).fetchone()
        return int(response.total_items) if response else 0

    async def update_user_password(
        self,
        conn: AsyncConnection,
        user: models.User,
        new_password: str,
    ) -> None:
        """Save new user password (this field is not a part of the user model)."""
        stmt = (
            sa.update(db_models.User.password)
            .where(db_models.User.id == user.id)
            .values(password=new_password)
        )
        await conn.execute(stmt)

    async def cast_uuids(self, conn: AsyncConnection, uuids: Collection[UUID]) -> set[int]:
        """Convert collection of `user_uuid` into set of `user_id`."""
        query = sa.select(db_models.User.id).where(db_models.User.uuid.in_(tuple(uuids)))
        response = (await conn.execute(query)).fetchall()
        return {row.id for row in response}
