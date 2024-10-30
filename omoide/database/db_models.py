"""Database implementation of the domain.

PostgreSQL specific because application needs arrays.
"""

from datetime import datetime
import os
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from omoide import const
from omoide import models

metadata = sa.MetaData()

HUGE = 1024
MEDIUM = 256
SMALL = 64


class Base(DeclarativeBase):
    """Base model type."""


class Role(Base):
    """User role model."""

    __tablename__ = 'user_roles'

    id: Mapped[int] = mapped_column(
        sa.Integer,
        primary_key=True,
        nullable=False,
        index=True,
        unique=True,
    )

    description: Mapped[str] = mapped_column(sa.String(SMALL), nullable=False)


class User(Base):
    """User model."""

    __tablename__ = 'users'

    # primary and foreign keys ------------------------------------------------

    id: Mapped[int] = mapped_column(
        sa.Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        index=True,
        unique=True,
    )

    uuid: Mapped[UUID] = mapped_column(pg.UUID(), nullable=False, index=True, unique=True)
    role: Mapped[models.Role] = mapped_column(
        sa.Integer, sa.ForeignKey('user_roles.id'), nullable=False, index=True
    )

    # fields ------------------------------------------------------------------

    login: Mapped[str] = mapped_column(
        sa.String(length=MEDIUM), nullable=False, unique=True, index=True
    )
    password: Mapped[str] = mapped_column(sa.String(length=HUGE), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(length=MEDIUM), nullable=False)
    auth_complexity: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    is_public: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, index=True)
    registered_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    # relations ---------------------------------------------------------------

    items: Mapped[list['Item']] = relationship(
        'Item',
        passive_deletes=True,
        primaryjoin='Item.owner_id==User.id',
        back_populates='owner',
        uselist=True,
    )

    media: Mapped['Media'] = relationship(
        'Media',
        passive_deletes=True,
        primaryjoin='Media.owner_id==User.id',
        back_populates='owner',
        uselist=True,
    )

    # methods -----------------------------------------------------------------

    def __repr__(self) -> str:
        """Return string representation."""
        return f'<User, id={self.id}, {self.uuid}, {self.name}>'

    @staticmethod
    def cast(row: sa.Row) -> models.User:
        """Convert to domain-level object."""
        return models.User(
            id=row.id,
            uuid=row.uuid,
            name=row.name,
            login=row.login,
            role=row.role,
            is_public=row.is_public,
            registered_at=row.registered_at,
            last_login=row.last_login,
        )


class PublicUsers(Base):
    """List of users who demonstrate their content publicly."""

    __tablename__ = 'public_users'

    # primary and foreign keys ------------------------------------------------
    number: Mapped[int] = mapped_column(
        sa.Integer, autoincrement=True, nullable=False, primary_key=True
    )

    user_uuid: Mapped[UUID] = mapped_column(
        pg.UUID(),
        sa.ForeignKey('users.uuid', ondelete='CASCADE'),
        nullable=False,
        index=True,
        unique=True,
    )


class ComputedTags(Base):
    """Combined tags of whole hierarchy of items.

    Hierarchy gets unwind and descendants inherit ancestors tags and uuids.

    Hierarchy:
        item1 with tags {'a', 'b'}
            └───item2 with tags {'b', 'c'}
                    └───item3 with tags {'c', 'd'}

    Computed tags example:
        item1: {'item1_uuid', 'a', 'b'}
        item2: {'item1_uuid', 'item2_uuid', 'a', 'b', 'c'}
        item3: {'item1_uuid', 'item2_uuid', 'item3_uuid', 'a', 'b', 'c', 'd'}
    """

    __tablename__ = 'computed_tags'

    # primary and foreign keys ------------------------------------------------

    item_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey('items.id', ondelete='CASCADE'),
        primary_key=True,
        nullable=False,
        index=True,
        unique=True,
    )

    # array fields ------------------------------------------------------------

    tags: Mapped[set[str]] = mapped_column(pg.ARRAY(sa.Text), nullable=False)

    # other -------------------------------------------------------------------

    __table_args__ = (sa.Index('ix_computed_tags', tags, postgresql_using='gin'),)


class KnownTags(Base):
    """User accessible cache of known tags.

    Requires:
        CREATE EXTENSION pg_trgm;
        CREATE EXTENSION btree_gin;
    """

    __tablename__ = 'known_tags'

    # primary and foreign keys ------------------------------------------------

    user_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey('users.id', ondelete='CASCADE'),
        index=True,
        primary_key=True,
    )
    tag: Mapped[str] = mapped_column(
        sa.String(MEDIUM), nullable=False, index=True, primary_key=True
    )

    # fields ------------------------------------------------------------------

    counter: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    __table_args__ = (
        sa.Index(
            'ix_known_tags',
            tag,
            postgresql_ops={'tag': 'text_pattern_ops'},
        ),
    )


class KnownTagsAnon(Base):
    """Anon user accessible cache of known tags."""

    __tablename__ = 'known_tags_anon'

    # primary and foreign keys ------------------------------------------------

    tag: Mapped[str] = mapped_column(
        sa.String(MEDIUM),
        unique=True,
        nullable=False,
        index=True,
        primary_key=True,
    )

    # fields ------------------------------------------------------------------

    counter: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    __table_args__ = (
        sa.Index('ix_known_tags_anon', tag, postgresql_ops={'tag': 'text_pattern_ops'}),
    )


class Status(Base):
    """Item status model."""

    __tablename__ = 'item_statuses'

    id: Mapped[int] = mapped_column(
        sa.Integer,
        primary_key=True,
        nullable=False,
        index=True,
        unique=True,
    )

    description: Mapped[str] = mapped_column(sa.String(SMALL), nullable=False)


class Item(Base):
    """Single unit of storage."""

    __tablename__ = 'items'

    # primary and foreign keys ------------------------------------------------

    id: Mapped[int] = mapped_column(
        sa.Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        index=True,
        unique=True,
    )

    uuid: Mapped[UUID] = mapped_column(pg.UUID(), nullable=False, index=True, unique=True)

    parent_id: Mapped[int | None] = mapped_column(
        sa.Integer,
        sa.ForeignKey('items.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
        unique=False,
    )

    owner_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        unique=False,
    )

    # fields ------------------------------------------------------------------

    status: Mapped[models.Status] = mapped_column(
        sa.Integer,
        sa.ForeignKey('item_statuses.id'),
        nullable=False,
        index=True,
    )
    number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    name: Mapped[str] = mapped_column(sa.String(MEDIUM), nullable=False)
    is_collection: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    content_ext: Mapped[str | None] = mapped_column(sa.String(SMALL), nullable=True)
    preview_ext: Mapped[str | None] = mapped_column(sa.String(SMALL), nullable=True)
    thumbnail_ext: Mapped[str | None] = mapped_column(sa.String(SMALL), nullable=True)

    # array fields ------------------------------------------------------------

    tags: Mapped[set[str]] = mapped_column(pg.ARRAY(sa.Text), nullable=False)
    permissions: Mapped[set[int]] = mapped_column(pg.ARRAY(sa.Integer), nullable=False)

    # methods -----------------------------------------------------------------

    def __repr__(self) -> str:
        """Return string representation."""
        return f'<Item, id={self.id}, {self.uuid}, {self.name!r}>'

    # relations ---------------------------------------------------------------

    owner: Mapped[User] = relationship(
        'User',
        passive_deletes=True,
        back_populates='items',
        primaryjoin='Item.owner_id==User.id',
        uselist=False,
    )

    metainfo: Mapped['Metainfo'] = relationship(
        'Metainfo', passive_deletes=True, back_populates='item', uselist=False
    )

    media: Mapped['Media'] = relationship(
        'Media', passive_deletes=True, back_populates='item', uselist=True
    )

    exif: Mapped['EXIF'] = relationship(
        'EXIF', passive_deletes=True, back_populates='item', uselist=False
    )

    # other -------------------------------------------------------------------

    __table_args__ = (
        sa.Index('ix_items_tags', tags, postgresql_using='gin'),
        sa.Index('ix_items_permissions', permissions, postgresql_using='gin'),
    )

    @staticmethod
    def cast(row: sa.Row) -> models.Item:
        """Convert to domain-level object."""
        return models.Item(
            id=row.id,
            uuid=row.uuid,
            parent_uuid=row.parent_uuid,
            owner_uuid=row.owner_uuid,
            name=row.name,
            number=row.number,
            is_collection=row.is_collection,
            content_ext=row.content_ext,
            preview_ext=row.preview_ext,
            thumbnail_ext=row.thumbnail_ext,
            tags=set(row.tags),
            permissions=set(row.permissions),
        )


class Metainfo(Base):
    """Meta information for items."""

    __tablename__ = 'item_metainfo'

    # primary and foreign keys ------------------------------------------------

    item_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey('items.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        primary_key=True,
        unique=True,
    )

    # fields ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    user_time: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=False), nullable=True)

    content_type: Mapped[str] = mapped_column(sa.String(length=SMALL), nullable=True)

    content_size: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    preview_size: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    thumbnail_size: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

    content_width: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    content_height: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    preview_width: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    preview_height: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    thumbnail_width: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    thumbnail_height: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

    # methods -----------------------------------------------------------------

    def __repr__(self) -> str:
        """Return string representation."""
        return f'<Metainfo, item_id={self.item_id}, {self.content_type!r}>'

    # relations ---------------------------------------------------------------

    item: Mapped[Item] = relationship(
        'Item', passive_deletes=True, back_populates='metainfo', uselist=False
    )

    @staticmethod
    def cast(row: sa.Row) -> models.Metainfo:
        """Convert to domain-level object."""
        return models.Metainfo(
            item_id=row.item_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            deleted_at=row.deleted_at,
            user_time=row.user_time,
            content_type=row.content_type,
            content_size=row.content_size,
            preview_size=row.preview_size,
            thumbnail_size=row.thumbnail_size,
            content_width=row.content_width,
            content_height=row.content_height,
            preview_width=row.preview_width,
            preview_height=row.preview_height,
            thumbnail_width=row.thumbnail_width,
            thumbnail_height=row.thumbnail_height,
        )


class ItemNote(Base):
    """Additional info for items."""

    __tablename__ = 'item_notes'

    # primary and foreign keys ------------------------------------------------

    id: Mapped[int] = mapped_column(
        sa.Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        index=True,
        unique=True,
    )

    item_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey('items.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    # fields ------------------------------------------------------------------

    key: Mapped[str] = mapped_column(sa.String(MEDIUM), nullable=False, index=True)
    value: Mapped[str] = mapped_column(sa.String(HUGE), nullable=False)

    # other -------------------------------------------------------------------

    __table_args__ = (sa.UniqueConstraint('item_id', 'key', name='item_notes_uc'),)


class Media(Base):
    """Converted content from user.

    Fully processed user content. If it's an image then it's already converted
    to a desired size. At this point we're using database as a storage. Worker
    process must perform download job and save data to actual storage device.
    """

    __tablename__ = 'media'

    # primary and foreign keys ------------------------------------------------

    id: Mapped[int] = mapped_column(
        sa.Integer,
        autoincrement=True,
        nullable=False,
        index=True,
        primary_key=True,
        unique=True,
    )

    # fields ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, index=True
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, index=True
    )
    error: Mapped[str] = mapped_column(sa.Text, nullable=True)

    owner_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        unique=False,
    )

    item_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey('items.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        unique=False,
    )

    media_type: Mapped[str] = mapped_column(sa.String(length=SMALL), nullable=False)
    content: Mapped[bytes] = mapped_column(pg.BYTEA, nullable=False)
    ext: Mapped[str] = mapped_column(sa.String(length=SMALL), nullable=False)

    # relations ---------------------------------------------------------------

    owner: Mapped[User] = relationship(
        'User',
        passive_deletes=True,
        back_populates='media',
        primaryjoin='Media.owner_id==User.id',
        uselist=False,
    )

    item: Mapped[Item] = relationship(
        'Item', passive_deletes=True, back_populates='media', uselist=False
    )


class EXIF(Base):
    """EXIF information for items."""

    __tablename__ = 'exif'

    # primary and foreign keys ------------------------------------------------

    item_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey('items.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        unique=True,
        primary_key=True,
    )

    # fields ------------------------------------------------------------------

    exif: Mapped[dict[str, Any]] = mapped_column(pg.JSONB, nullable=False)

    # relations ---------------------------------------------------------------

    item: Mapped[Item] = relationship(
        'Item', passive_deletes=True, back_populates='exif', uselist=False
    )


class SignatureMD5(Base):
    """MD5 hash for item content."""

    __tablename__ = 'signatures_md5'

    # primary and foreign keys ------------------------------------------------

    item_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey('items.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        unique=True,
        primary_key=True,
    )

    # fields ------------------------------------------------------------------

    signature: Mapped[str] = mapped_column(sa.CHAR(32), nullable=False, index=True)


class SignatureCRC32(Base):
    """CRC32 hash for item content."""

    __tablename__ = 'signatures_crc32'

    # primary and foreign keys ------------------------------------------------

    item_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey('items.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        unique=True,
        primary_key=True,
    )

    # fields ------------------------------------------------------------------

    signature: Mapped[int] = mapped_column(sa.BigInteger, nullable=False, index=True)


class RegisteredWorkers(Base):
    """All allowed workers."""

    __tablename__ = 'registered_workers'

    # primary and foreign keys ------------------------------------------------

    id: Mapped[int] = mapped_column(
        sa.Integer,
        autoincrement=True,
        nullable=False,
        index=True,
        primary_key=True,
        unique=True,
    )

    # fields ------------------------------------------------------------------

    worker_name: Mapped[str] = mapped_column(
        sa.String(MEDIUM), nullable=False, index=True, unique=True
    )

    last_restart: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, index=True
    )


class SerialLock(Base):
    """Lock for serial workers."""

    __tablename__ = 'serial_lock'

    # primary and foreign keys ------------------------------------------------

    id: Mapped[int] = mapped_column(
        sa.Integer,
        autoincrement=True,
        nullable=False,
        index=True,
        primary_key=True,
        unique=True,
    )

    # fields ------------------------------------------------------------------

    worker_name: Mapped[str] = mapped_column(sa.String(MEDIUM), nullable=True)

    last_update: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, index=True
    )


class SerialOperation(Base):
    """Global operations that run in serial."""

    __tablename__ = 'serial_operations'

    # primary and foreign keys ------------------------------------------------

    id: Mapped[int] = mapped_column(
        sa.Integer,
        autoincrement=True,
        nullable=False,
        index=True,
        primary_key=True,
        unique=True,
    )

    # fields ------------------------------------------------------------------

    name: Mapped[str] = mapped_column(sa.String(MEDIUM), nullable=False)
    worker_name: Mapped[str] = mapped_column(sa.String(MEDIUM), nullable=True)
    status: Mapped[str] = mapped_column(sa.String(SMALL), nullable=False)
    extras: Mapped[dict[str, Any]] = mapped_column(pg.JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    log: Mapped[str] = mapped_column(sa.Text, nullable=True)


if __name__ == '__main__':
    db_url = os.environ[const.ENV_DB_URL_ADMIN]
    engine = sa.create_engine(db_url, echo=True)
    metadata.create_all(engine, checkfirst=True)
