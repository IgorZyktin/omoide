"""Repository that performs special operations for tests.
"""
from uuid import UUID

import sqlalchemy as sa

from omoide.storage.interfaces.abs_storage import AbsStorage
from omoide import custom_logging
from omoide.storage.database import db_models

LOG = custom_logging.get_logger(__name__)


class RepositoryForTests(AbsStorage):
    """Repository that performs special operations for tests."""

    async def drop_known_tags_for_known_user(self, user_uuid: UUID) -> None:
        """Delete all known tags for known user."""
        stmt = sa.delete(
            db_models.KnownTags
        ).where(
            db_models.KnownTags.user_uuid == user_uuid
        )
        await self.db.execute(stmt)

    async def drop_known_tags_for_anon_user(self) -> None:
        """Delete all known tags for anon user."""
        stmt = sa.delete(db_models.KnownTagsAnon)
        await self.db.execute(stmt)

    async def insert_known_tags_for_known_user(
            self,
            user_uuid: UUID,
            tags: dict[str, int],
    ) -> None:
        """Add known tags for known user."""
        stmt = sa.insert(
            db_models.KnownTags
        ).values(
            [(str(user_uuid), tag, counter) for tag, counter in tags.items()]
        )
        await self.db.execute(stmt)

    async def insert_known_tags_for_anon_user(
            self,
            tags: dict[str, int],
    ) -> None:
        """Add known tags for anon user."""
        stmt = sa.insert(
            db_models.KnownTagsAnon
        ).values(
            list(tags.items())
        )
        await self.db.execute(stmt)
