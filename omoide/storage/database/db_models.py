"""Database implementation of the domain.

PostgreSQL specific because application needs arrays.
"""
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# TODO - move actual models here
from omoide.storage.database import models

Base = models.Base
EXIF = models.EXIF
KnownTags = models.KnownTags
KnownTagsAnon = models.KnownTagsAnon
Media = models.Media
ManualCopy = models.ManualCopy
Metainfo = models.Metainfo
Item = models.Item
User = models.User


class CommandCopyThumbnail(Base):
    """Operation of copying thumbnail from one item to another."""
    __tablename__ = 'commands_copy_thumbnail'

    # primary and foreign keys ------------------------------------------------

    id: int = sa.Column(sa.BigInteger,
                        autoincrement=True,
                        nullable=False,
                        index=True,
                        primary_key=True)

    # fields ------------------------------------------------------------------

    created_at: datetime = sa.Column(sa.DateTime(timezone=True),
                                     nullable=False,
                                     index=True)
    processed_at: datetime | None = sa.Column(sa.DateTime(timezone=True),
                                              nullable=True)
    error: str = sa.Column(sa.Text, nullable=False)

    owner_uuid: UUID = sa.Column(pg.UUID(),
                                 sa.ForeignKey('users.uuid',
                                               ondelete='CASCADE'),
                                 nullable=False)

    source_uuid: UUID = sa.Column(pg.UUID(),
                                  sa.ForeignKey('items.uuid',
                                                ondelete='CASCADE'),
                                  nullable=False)

    target_uuid: UUID = sa.Column(pg.UUID(),
                                  sa.ForeignKey('items.uuid',
                                                ondelete='CASCADE'),
                                  nullable=False)
    ext: str = sa.Column(sa.String(length=16), nullable=False)


class Stats(Base):
    """Command statistics."""
    __tablename__ = 'stats'

    # primary and foreign keys ------------------------------------------------

    id: int = sa.Column(sa.BigInteger,
                        autoincrement=True,
                        nullable=False,
                        index=True,
                        primary_key=True)

    # fields ------------------------------------------------------------------

    started_at: datetime = sa.Column(sa.DateTime(timezone=True),
                                     nullable=False,
                                     index=True)
    finished_at: datetime = sa.Column(sa.DateTime(timezone=True),
                                      nullable=False)
    duration: float = sa.Column(sa.Float, nullable=False)
    operation: str = sa.Column(sa.String(length=255), nullable=False)
    is_success = sa.Column(sa.Boolean, nullable=False)
    extras: dict = sa.Column(pg.JSONB, nullable=False)
