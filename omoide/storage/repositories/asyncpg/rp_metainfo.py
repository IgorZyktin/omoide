# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on metainfo.
"""
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from omoide import domain
from omoide import utils
from omoide.domain import interfaces
from omoide.storage.database import models


class MetainfoRepository(interfaces.AbsMetainfoRepository):
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
            uuid: UUID,
    ) -> Optional[domain.Metainfo]:
        """Return metainfo or None."""
        stmt = sa.select(
            models.Metainfo
        ).where(
            models.Metainfo.item_uuid == uuid
        )

        response = await self.db.fetch_one(stmt)

        if response is None:
            return None

        return domain.Metainfo(
            item_uuid=response['item_uuid'],

            created_at=response['created_at'],
            updated_at=response['updated_at'],
            deleted_at=response['deleted_at'],
            user_time=response['user_time'],

            width=response['width'],
            height=response['height'],
            duration=response['duration'],
            resolution=response['resolution'],
            media_type=response['media_type'],

            author=response['author'],
            author_url=response['author_url'],
            saved_from_url=response['saved_from_url'],
            description=response['description'],

            extras=response['extras'],

            content_size=response['content_size'],
            preview_size=response['preview_size'],
            thumbnail_size=response['thumbnail_size'],
        )

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
            **metainfo.dict(exclude={'item_uuid', 'created_at'})
        )

        await self.db.execute(stmt)

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

        all_tags = {
            *item.tags,
            *parent_tags,
            str(item.uuid),
        }

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

    async def update_computed_permissions(
            self,
            user: domain.User,
            item: domain.Item,
    ) -> None:
        """Update computed permissions for this item."""
        insert = pg_insert(
            models.ComputedPermissions
        ).values(
            item_uuid=item.uuid,
            permissions=[str(x) for x in item.permissions],
        )

        stmt = insert.on_conflict_do_update(
            index_elements=[models.ComputedPermissions.item_uuid],
            set_={
                'permissions': insert.excluded.permissions,
            }
        )

        await self.db.execute(stmt)

    async def increase_known_tags_for_known_user(
            self,
            user_uuid: UUID,
            tags: list[str],
    ) -> None:
        """Update known tags using this item."""
        for tag in tags:
            tag = tag.lower()
            insert = pg_insert(
                models.KnownTags
            ).values(
                user_uuid=user_uuid,
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

    async def decrease_known_tags_for_known_user(
            self,
            user_uuid: UUID,
            tags: list[str],
    ) -> None:
        """Decrease counters for known tags using this item."""
        for tag in tags:
            tag = tag.lower()
            stmt = sa.update(
                models.KnownTags
            ).where(
                models.KnownTags.user_uuid == user_uuid,
                models.KnownTags.tag == tag,
            ).values(
                counter=models.KnownTags.counter - 1,
            )

            await self.db.execute(stmt)

    async def drop_unused_tags_for_known_user(
            self,
            user_uuid: UUID,
    ) -> None:
        """Drop tags with counter less of equal to 0."""
        stmt = sa.delete(
            models.KnownTags
        ).where(
            models.KnownTags.user_uuid == user_uuid,
            models.KnownTags.counter <= 0,
        )

        await self.db.execute(stmt)

    async def increase_known_tags_for_anon_user(
            self,
            tags: list[str],
    ) -> None:
        """Update known tags using this item."""
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

    async def decrease_known_tags_for_anon_user(
            self,
            tags: list[str],
    ) -> None:
        """Decrease counters for known tags using this item."""
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

    async def drop_unused_tags_for_anon_user(
            self,
            user_uuid: UUID,
    ) -> None:
        """Drop tags with counter less of equal to 0."""
        stmt = sa.delete(
            models.KnownTagsAnon
        ).where(
            models.KnownTagsAnon.counter <= 0,
        )

        await self.db.execute(stmt)
