"""Database implementation of the domain.

PostgreSQL specific because application needs arrays.
"""
from datetime import datetime

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
                                      nullable=False,
                                      index=True)
    duration: float = sa.Column(sa.Float, nullable=False)
    operation: str = sa.Column(sa.String(length=255), nullable=False)
    is_success = sa.Column(sa.Boolean, nullable=False)
    error = sa.Column(sa.Text, nullable=False)
    extras: dict = sa.Column(pg.JSONB, nullable=False)
