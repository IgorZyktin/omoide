# -*- coding: utf-8 -*-
"""Database implementation of the domain.

PostgreSQL specific because application needs arrays.
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from omoide.infra import impl

metadata = sa.MetaData()


class StorageModel(DeclarativeBase):
    """Base class for all storage models."""


class EXIF(StorageModel):
    """EXIF information for items."""
    __tablename__ = 'exif'

    # primary and foreign keys ------------------------------------------------

    item_uuid: Mapped[impl.UUID] = mapped_column(
        sa.Column(
            pg.UUID(),
            sa.ForeignKey('items.uuid', ondelete='CASCADE'),
            nullable=False,
            index=True,
            primary_key=True,
        )
    )

    # fields ------------------------------------------------------------------

    exif: Mapped[impl.JSON] = mapped_column(
        sa.Column(
            pg.JSONB,
            nullable=False,
        )
    )

    # relations ---------------------------------------------------------------

    item: Mapped['Item'] = relationship(
        'Item',
        passive_deletes=True,
        back_populates='exif',
        uselist=False,
    )
