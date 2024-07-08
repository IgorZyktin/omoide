"""Repository that perform CRUD operations on metainfo."""
from uuid import UUID

import sqlalchemy as sa

from omoide import exceptions
from omoide import models
from omoide import utils
from omoide.storage.asyncpg_storage import AsyncpgStorage
from omoide.storage.database import db_models
from omoide.storage import interfaces


class MetainfoRepo(interfaces.AbsMetainfoRepo, AsyncpgStorage):
    """Repository that perform CRUD operations on metainfo."""

    async def create_empty_metainfo(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> None:
        """Create metainfo with blank fields."""
        stmt = sa.insert(
            db_models.Metainfo
        ).values(
            item_uuid=item_uuid,
            created_at=utils.now(),
            updated_at=utils.now(),
            extras={},
        )

        await self.db.execute(stmt)

    async def read_metainfo(self, item_uuid: UUID) -> models.Metainfo:
        """Return metainfo."""
        stmt = sa.select(
            db_models.Metainfo
        ).where(
            db_models.Metainfo.item_uuid == item_uuid
        )

        response = await self.db.fetch_one(stmt)

        if response is None:
            msg = 'Metainfo for item {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)

        return models.Metainfo(**response)

    async def update_metainfo(
        self,
        user: models.User,
        item_uuid: UUID,
        metainfo: models.Metainfo,
    ) -> None:
        """Update metainfo."""
        stmt = sa.update(
            db_models.Metainfo
        ).where(
            db_models.Metainfo.item_uuid == item_uuid
        ).values(
            **metainfo.model_dump(exclude={'item_uuid', 'created_at'})
        ).returning(1)

        response = await self.db.execute(stmt)

        if response is None:
            msg = 'Metainfo for item {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)

    async def mark_metainfo_updated(self, item_uuid: UUID) -> None:
        """Set last updated to current datetime."""
        stmt = sa.update(
            db_models.Metainfo
        ).values(
            updated_at=utils.now()
        ).where(
            db_models.Metainfo.item_uuid == item_uuid
        ).returning(1)

        response = await self.db.execute(stmt)

        if response is None:
            msg = 'Metainfo for item {item_uuid} does not exist'
            raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)

    async def update_metainfo_extras(
        self,
        uuid: UUID,
        new_extras: dict[str, None | int | float | str | bool],
    ) -> None:
        """Add new data to extras."""
        for key, value in new_extras.items():
            stmt = sa.update(
                db_models.Metainfo
            ).where(
                db_models.Metainfo.item_uuid == uuid
            ).values(
                extras=sa.func.jsonb_set(
                    db_models.Metainfo.extras,
                    [key],
                    f'"{value}"' if isinstance(value, str) else value,
                )
            )
            await self.db.execute(stmt)

    # async def read_children_to_download(
    #     self,
    #     user: models.User,
    #     item: domain.Item,
    # ) -> list[dict[str, UUID | str | int]]:
    #     """Return some components of the given item children with metainfo."""
    #     stmt = sa.select(
    #         db_models.Item.uuid,
    #         db_models.Metainfo.content_size,
    #         db_models.Item.content_ext,
    #     ).join(
    #         db_models.Metainfo,
    #         db_models.Metainfo.item_uuid == db_models.Item.uuid,
    #         isouter=True,
    #     )
    #
    #     stmt = queries.ensure_user_has_permissions(user, stmt)
    #
    #     stmt = stmt.where(
    #         db_models.Item.parent_uuid == item.uuid,
    #         db_models.Item.is_collection == False,  # noqa
    #         db_models.Item.content_ext != None,  # noqa
    #         db_models.Metainfo.content_size != None,  # noqa
    #     ).order_by(
    #         db_models.Item.number,
    #     )
    #
    #     response = await self.db.fetch_all(stmt)
    #     return [dict(x) for x in response]  # type: ignore

    # @staticmethod
    # def gather_tags(
    #     parent_uuid: Optional[UUID],
    #     parent_tags: list[str],
    #     item_uuid: UUID,
    #     item_tags: list[str],
    # ) -> tuple[str, ...]:
    #     """Combine parent tags with item tags."""
    #     all_tags = {
    #         *(x.lower() for x in item_tags),
    #         str(item_uuid),
    #     }
    #
    #     if parent_uuid is not None:
    #         clean_parent_uuid = str(parent_uuid).lower()
    #         clean_tags = (
    #             lower
    #             for x in parent_tags
    #             if (lower := x.lower()) != clean_parent_uuid
    #         )
    #         all_tags.update(clean_tags)
    #
    #     return tuple(all_tags)

    # async def update_computed_tags(
    #     self,
    #     user: models.User,
    #     item: domain.Item,
    # ) -> None:
    #     """Update computed tags for this item."""
    #     parent_tags = []
    #
    #     if item.parent_uuid is not None:
    #         parent_tags_stmt = sa.select(
    #             db_models.ComputedTags.tags
    #         ).where(
    #             db_models.ComputedTags.item_uuid == item.parent_uuid
    #         )
    #         parent_tags_response = await self.db.execute(parent_tags_stmt)
    #
    #         if parent_tags_response:
    #             parent_tags = parent_tags_response
    #
    #     all_tags = self.gather_tags(
    #         parent_uuid=item.parent_uuid,
    #         parent_tags=parent_tags,
    #         item_uuid=item.uuid,
    #         item_tags=item.tags,
    #     )
    #
    #     insert = pg_insert(
    #         db_models.ComputedTags
    #     ).values(
    #         item_uuid=item.uuid,
    #         tags=tuple(all_tags),
    #     )
    #
    #     stmt = insert.on_conflict_do_update(
    #         index_elements=[db_models.ComputedTags.item_uuid],
    #         set_={
    #             'tags': insert.excluded.tags,
    #         }
    #     )
    #
    #     await self.db.execute(stmt)

    # async def _increase_known_tags_for_known_user(
    #     self,
    #     user: models.User,
    #     tags: Collection[str],
    # ) -> None:
    #     """Update known tags using this item."""
    #     assert user.is_not_anon
    #
    #     for tag in tags:
    #         tag = tag.lower()
    #         insert = pg_insert(
    #             db_models.KnownTags
    #         ).values(
    #             user_uuid=user.uuid,
    #             tag=tag,
    #             counter=1,
    #         )
    #
    #         stmt = insert.on_conflict_do_update(
    #             index_elements=[
    #                 db_models.KnownTags.user_uuid,
    #                 db_models.KnownTags.tag,
    #             ],
    #             set_={
    #                 'counter': db_models.KnownTags.counter + 1,
    #             }
    #         )
    #
    #         await self.db.execute(stmt)

    # async def _decrease_known_tags_for_known_user(
    #     self,
    #     user: models.User,
    #     tags: Collection[str],
    # ) -> None:
    #     """Decrease counters for known tags using this item."""
    #     assert user.is_not_anon
    #
    #     for tag in tags:
    #         tag = tag.lower()
    #         stmt = sa.update(
    #             db_models.KnownTags
    #         ).where(
    #             db_models.KnownTags.user_uuid == user.uuid,
    #             db_models.KnownTags.tag == tag,
    #         ).values(
    #             counter=db_models.KnownTags.counter - 1,
    #         )
    #
    #         await self.db.execute(stmt)

    # async def apply_new_known_tags(
    #     self,
    #     users: Collection[models.User],
    #     tags_added: Collection[str],
    #     tags_deleted: Collection[str],
    # ) -> None:
    #     """Update counters for known tags."""
    #     for user in users:
    #         if tags_added:
    #             if user.is_anon:
    #                 await self._increase_known_tags_for_anon_user(
    #                     user, tags_added)
    #             else:
    #                 await self._increase_known_tags_for_known_user(
    #                     user, tags_added)
    #
    #         if tags_deleted:
    #             if user.is_anon:
    #                 await self._decrease_known_tags_for_anon_user(
    #                     user, tags_deleted)
    #             else:
    #                 await self._decrease_known_tags_for_known_user(
    #                     user, tags_deleted)
    #
    # async def drop_unused_tags(
    #     self,
    #     users: Collection[models.User],
    #     public_users: set[UUID],
    # ) -> None:
    #     """Drop tags with counter less of equal to 0."""
    #     for user in users:
    #         if user.is_not_anon:
    #             stmt = sa.delete(
    #                 db_models.KnownTags
    #             ).where(
    #                 db_models.KnownTags.user_uuid == user.uuid,
    #                 db_models.KnownTags.counter <= 0,
    #             )
    #             await self.db.execute(stmt)
    #
    #         elif user.is_anon or user.uuid in public_users:
    #             stmt = sa.delete(
    #                 db_models.KnownTagsAnon
    #             ).where(
    #                 db_models.KnownTagsAnon.counter <= 0,
    #             )
    #             await self.db.execute(stmt)
    #
    # async def _increase_known_tags_for_anon_user(
    #     self,
    #     user: models.User,
    #     tags: Collection[str],
    # ) -> None:
    #     """Update known tags using this item."""
    #     assert user.is_anon
    #
    #     for tag in tags:
    #         tag = tag.lower()
    #         insert = pg_insert(
    #             db_models.KnownTagsAnon
    #         ).values(
    #             tag=tag,
    #             counter=1,
    #         )
    #
    #         stmt = insert.on_conflict_do_update(
    #             index_elements=[
    #                 db_models.KnownTagsAnon.tag,
    #             ],
    #             set_={
    #                 'counter': db_models.KnownTagsAnon.counter + 1,
    #             }
    #         )
    #
    #         await self.db.execute(stmt)
    #
    # async def _decrease_known_tags_for_anon_user(
    #     self,
    #     user: models.User,
    #     tags: Collection[str],
    # ) -> None:
    #     """Decrease counters for known tags using this item."""
    #     assert user.is_anon
    #
    #     for tag in tags:
    #         tag = tag.lower()
    #         stmt = sa.update(
    #             db_models.KnownTagsAnon
    #         ).where(
    #             db_models.KnownTagsAnon.tag == tag,
    #         ).values(
    #             counter=db_models.KnownTagsAnon.counter - 1,
    #         )
    #
    #         await self.db.execute(stmt)

    # async def start_long_job(
    #     self,
    #     name: str,
    #     user_uuid: UUID,
    #     target_uuid: UUID,
    #     added: Collection[str],
    #     deleted: Collection[str],
    #     status: str,
    #     started: datetime.datetime,
    #     extras: dict[str, int | float | bool | str | None],
    # ) -> int:
    #     """Start long job."""
    #     stmt = sa.insert(
    #         db_models.LongJob
    #     ).values(
    #         name=name,
    #         user_uuid=user_uuid,
    #         target_uuid=target_uuid,
    #         added=list(added),
    #         deleted=list(deleted),
    #         status=status,
    #         started=started,
    #         duration=None,
    #         operations=None,
    #         extras=extras,
    #         error='',
    #     ).returning(
    #         db_models.LongJob.id
    #     )
    #
    #     return int(await self.db.execute(stmt))
    #
    # async def finish_long_job(
    #     self,
    #     id: int,
    #     status: str,
    #     duration: float,
    #     operations: int,
    #     error: str,
    # ) -> None:
    #     """Finish long job."""
    #     stmt = sa.update(
    #         db_models.LongJob
    #     ).values(
    #         status=status,
    #         duration=duration,
    #         operations=operations,
    #         error=error,
    #     ).where(
    #         db_models.LongJob.id == id
    #     )
    #
    #     await self.db.execute(stmt)
