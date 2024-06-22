"""Repository that perform CRUD operations on metainfo.
"""
import datetime
from typing import Collection
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from omoide import domain
from omoide import utils
from omoide.domain import exceptions
from omoide.domain import interfaces
from omoide.domain.core import core_models
from omoide.storage.database import models
from omoide.storage.repositories.asyncpg import queries


class MetainfoRepo(interfaces.AbsMetainfoRepo):
    """Repository that perform CRUD operations on metainfo."""

    async def create_empty_metainfo(
            self,
            user: domain.User,
            item: domain.Item,
    ) -> bool:
        """Create metainfo with blank fields."""
        stmt = sa.insert(
            models.Metainfo
        ).values(
            item_uuid=item.uuid,
            created_at=utils.now(),
            updated_at=utils.now(),
            extras={},
        )

        await self.db.execute(stmt)

        return True

    async def read_metainfo(
            self,
            item_uuid: UUID,
    ) -> core_models.Metainfo:
        """Return metainfo."""
        stmt = sa.select(
            models.Metainfo
        ).where(
            models.Metainfo.item_uuid == item_uuid
        )

        response = await self.db.fetch_one(stmt)

        if response is None:
            raise exceptions.MetainfoNotExistError(item_uuid=item_uuid)

        return core_models.Metainfo(**response)

    async def read_children_to_download(
            self,
            user: domain.User,
            item: domain.Item,
    ) -> list[dict[str, UUID | str | int]]:
        """Return some components of the given item children with metainfo."""
        stmt = sa.select(
            models.Item.uuid,
            models.Metainfo.content_size,
            models.Item.content_ext,
        ).join(
            models.Metainfo,
            models.Metainfo.item_uuid == models.Item.uuid,
            isouter=True,
        )

        stmt = queries.ensure_user_has_permissions(user, stmt)

        stmt = stmt.where(
            models.Item.parent_uuid == item.uuid,
            models.Item.is_collection == False,  # noqa
            models.Item.content_ext != None,  # noqa
            models.Metainfo.content_size != None,  # noqa
        ).order_by(
            models.Item.number,
        )

        response = await self.db.fetch_all(stmt)
        return [dict(x) for x in response]  # type: ignore

    async def update_metainfo(
            self,
            user: domain.User,
            metainfo: domain.Metainfo,
    ) -> None:
        """Update metainfo and return true on success."""
        stmt = sa.update(
            models.Metainfo
        ).where(
            models.Metainfo.item_uuid == metainfo.item_uuid
        ).values(
            **metainfo.model_dump(exclude={'item_uuid', 'created_at'})
        )

        await self.db.execute(stmt)

    @staticmethod
    def gather_tags(
            parent_uuid: Optional[UUID],
            parent_tags: list[str],
            item_uuid: UUID,
            item_tags: list[str],
    ) -> tuple[str, ...]:
        """Combine parent tags with item tags."""
        all_tags = {
            *(x.lower() for x in item_tags),
            str(item_uuid),
        }

        if parent_uuid is not None:
            clean_parent_uuid = str(parent_uuid).lower()
            clean_tags = (
                lower
                for x in parent_tags
                if (lower := x.lower()) != clean_parent_uuid
            )
            all_tags.update(clean_tags)

        return tuple(all_tags)

    async def update_computed_tags(
            self,
            user: domain.User,
            item: domain.Item,
    ) -> None:
        """Update computed tags for this item."""
        parent_tags = []

        if item.parent_uuid is not None:
            parent_tags_stmt = sa.select(
                models.ComputedTags.tags
            ).where(
                models.ComputedTags.item_uuid == item.parent_uuid
            )
            parent_tags_response = await self.db.execute(parent_tags_stmt)

            if parent_tags_response:
                parent_tags = parent_tags_response

        all_tags = self.gather_tags(
            parent_uuid=item.parent_uuid,
            parent_tags=parent_tags,
            item_uuid=item.uuid,
            item_tags=item.tags,
        )

        insert = pg_insert(
            models.ComputedTags
        ).values(
            item_uuid=item.uuid,
            tags=tuple(all_tags),
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[models.ComputedTags.item_uuid],
            set_={
                'tags': insert.excluded.tags,
            }
        )

        await self.db.execute(stmt)

    async def _increase_known_tags_for_known_user(
            self,
            user: domain.User,
            tags: Collection[str],
    ) -> None:
        """Update known tags using this item."""
        assert user.is_registered

        for tag in tags:
            tag = tag.lower()
            insert = pg_insert(
                models.KnownTags
            ).values(
                user_uuid=user.uuid,
                tag=tag,
                counter=1,
            )

            stmt = insert.on_conflict_do_update(
                index_elements=[
                    models.KnownTags.user_uuid,
                    models.KnownTags.tag,
                ],
                set_={
                    'counter': models.KnownTags.counter + 1,
                }
            )

            await self.db.execute(stmt)

    async def _decrease_known_tags_for_known_user(
            self,
            user: domain.User,
            tags: Collection[str],
    ) -> None:
        """Decrease counters for known tags using this item."""
        assert user.is_registered

        for tag in tags:
            tag = tag.lower()
            stmt = sa.update(
                models.KnownTags
            ).where(
                models.KnownTags.user_uuid == user.uuid,
                models.KnownTags.tag == tag,
            ).values(
                counter=models.KnownTags.counter - 1,
            )

            await self.db.execute(stmt)

    async def apply_new_known_tags(
            self,
            users: Collection[domain.User],
            tags_added: Collection[str],
            tags_deleted: Collection[str],
    ) -> None:
        """Update counters for known tags."""
        for user in users:
            if tags_added:
                if user.is_not_registered:
                    await self._increase_known_tags_for_anon_user(
                        user, tags_added)
                else:
                    await self._increase_known_tags_for_known_user(
                        user, tags_added)

            if tags_deleted:
                if user.is_not_registered:
                    await self._decrease_known_tags_for_anon_user(
                        user, tags_deleted)
                else:
                    await self._decrease_known_tags_for_known_user(
                        user, tags_deleted)

    async def drop_unused_tags(
            self,
            users: Collection[domain.User],
            public_users: set[UUID],
    ) -> None:
        """Drop tags with counter less of equal to 0."""
        for user in users:
            if user.is_registered:
                stmt = sa.delete(
                    models.KnownTags
                ).where(
                    models.KnownTags.user_uuid == user.uuid,
                    models.KnownTags.counter <= 0,
                )
                await self.db.execute(stmt)

            elif user.is_not_registered or user.uuid in public_users:
                stmt = sa.delete(
                    models.KnownTagsAnon
                ).where(
                    models.KnownTagsAnon.counter <= 0,
                )
                await self.db.execute(stmt)

    async def _increase_known_tags_for_anon_user(
            self,
            user: domain.User,
            tags: Collection[str],
    ) -> None:
        """Update known tags using this item."""
        assert user.is_not_registered

        for tag in tags:
            tag = tag.lower()
            insert = pg_insert(
                models.KnownTagsAnon
            ).values(
                tag=tag,
                counter=1,
            )

            stmt = insert.on_conflict_do_update(
                index_elements=[
                    models.KnownTagsAnon.tag,
                ],
                set_={
                    'counter': models.KnownTagsAnon.counter + 1,
                }
            )

            await self.db.execute(stmt)

    async def _decrease_known_tags_for_anon_user(
            self,
            user: domain.User,
            tags: Collection[str],
    ) -> None:
        """Decrease counters for known tags using this item."""
        assert user.is_not_registered

        for tag in tags:
            tag = tag.lower()
            stmt = sa.update(
                models.KnownTagsAnon
            ).where(
                models.KnownTagsAnon.tag == tag,
            ).values(
                counter=models.KnownTagsAnon.counter - 1,
            )

            await self.db.execute(stmt)

    async def mark_metainfo_updated(
            self,
            uuid: UUID,
            now: datetime.datetime,
    ) -> None:
        """Set last updated at given tine for the item."""
        stmt = sa.update(
            models.Metainfo
        ).values(
            updated_at=now
        ).where(
            models.Metainfo.item_uuid == uuid
        )

        await self.db.execute(stmt)

    async def update_metainfo_extras(
            self,
            uuid: UUID,
            new_extras: dict[str, None | int | float | str | bool],
    ) -> None:
        """Add new data to extras."""
        for key, value in new_extras.items():
            stmt = sa.update(
                models.Metainfo
            ).where(
                models.Metainfo.item_uuid == uuid
            ).values(
                extras=sa.func.jsonb_set(
                    models.Metainfo.extras,
                    [key],
                    f'"{value}"' if isinstance(value, str) else value,
                )
            )
            await self.db.execute(stmt)

    async def start_long_job(
            self,
            name: str,
            user_uuid: UUID,
            target_uuid: UUID,
            added: Collection[str],
            deleted: Collection[str],
            status: str,
            started: datetime.datetime,
            extras: dict[str, int | float | bool | str | None],
    ) -> int:
        """Start long job."""
        stmt = sa.insert(
            models.LongJob
        ).values(
            name=name,
            user_uuid=user_uuid,
            target_uuid=target_uuid,
            added=list(added),
            deleted=list(deleted),
            status=status,
            started=started,
            duration=None,
            operations=None,
            extras=extras,
            error='',
        ).returning(
            models.LongJob.id
        )

        return int(await self.db.execute(stmt))

    async def finish_long_job(
            self,
            id: int,
            status: str,
            duration: float,
            operations: int,
            error: str,
    ) -> None:
        """Finish long job."""
        stmt = sa.update(
            models.LongJob
        ).values(
            status=status,
            duration=duration,
            operations=operations,
            error=error,
        ).where(
            models.LongJob.id == id
        )

        await self.db.execute(stmt)
