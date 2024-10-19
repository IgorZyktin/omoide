"""Database implementation of the domain.

PostgreSQL specific because application needs arrays.
"""

import os
from datetime import datetime
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from omoide import const
from omoide import models

metadata = sa.MetaData()
Base = declarative_base(metadata=metadata)

HUGE = 1024
MEDIUM = 256
SMALL = 64


class Role(Base):
    """User role model."""

    __tablename__ = 'user_roles'

    id: Mapped[int] = mapped_column(
        sa.Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(sa.VARCHAR(SMALL), nullable=False)


class User(Base):
    """User model."""

    __tablename__ = 'users'

    # primary and foreign keys ------------------------------------------------

    id: Mapped[int] = mapped_column(
        sa.Integer,
        # TODO - actually make it a primary key
        # primary_key=True,  noqa: ERA001
        autoincrement=True,
        nullable=False,
        index=True,
        unique=True,
    )

    uuid: Mapped[UUID] = mapped_column(
        # TODO - remove from primary keys
        pg.UUID(),
        primary_key=True,
        nullable=False,
        index=True,
        unique=True,
    )

    role: Mapped[models.Role] = mapped_column(
        sa.Integer, sa.ForeignKey('user_roles.id'), nullable=False
    )

    # fields ------------------------------------------------------------------

    login: Mapped[str] = mapped_column(
        sa.String(length=MEDIUM), nullable=False, unique=True
    )
    password: Mapped[str] = mapped_column(
        sa.String(length=HUGE), nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(length=MEDIUM), nullable=False)
    auth_complexity: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    is_public: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, index=True
    )

    # relations ---------------------------------------------------------------

    items: Mapped[list['Item']] = relationship(
        'Item',
        passive_deletes=True,
        primaryjoin='Item.owner_uuid==User.uuid',
        back_populates='owner',
        uselist=True,
    )

    media: Mapped['Media'] = relationship(
        'Media',
        passive_deletes=True,
        primaryjoin='Media.owner_uuid==User.uuid',
        back_populates='owner',
        uselist=True,
    )

    # methods -----------------------------------------------------------------

    def __repr__(self) -> str:
        """Return string representation."""
        return f'<User, {self.uuid}, {self.name}>'

    # Feature: Add email field so users could change passwords by themselves

    # Feature: Add registered_at field to be able
    # to see how long user uses the site

    # Feature: Add last_login field to know when user was active last time

    # Feature: Add is_confirmed field to switch between demo and active users.
    # Activation links can be sent via emails


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

    item_uuid: Mapped[UUID] = mapped_column(
        pg.UUID(),
        sa.ForeignKey('items.uuid', ondelete='CASCADE'),
        primary_key=True,
        nullable=False,
        index=True,
        unique=True,
    )

    # array fields ------------------------------------------------------------

    tags: Mapped[list[str]] = mapped_column(pg.ARRAY(sa.Text), nullable=False)

    # other -------------------------------------------------------------------

    __table_args__ = (
        sa.Index('ix_computed_tags', tags, postgresql_using='gin'),
    )


class OrphanFiles(Base):
    """Model that tracks files of already deleted items.

    Has not foreign keys because user/item could already be deleted.
    """

    __tablename__ = 'orphan_files'

    # primary and foreign keys ------------------------------------------------

    id: Mapped[int] = mapped_column(
        sa.BigInteger,
        autoincrement=True,
        nullable=False,
        index=True,
        primary_key=True,
    )

    # fields ------------------------------------------------------------------

    media_type: Mapped[str] = mapped_column(
        sa.Enum(
            const.CONTENT, const.PREVIEW, const.THUMBNAIL, name='media_type'
        )
    )

    owner_uuid: Mapped[UUID] = mapped_column(
        pg.UUID(), nullable=False, index=True
    )

    item_uuid: Mapped[UUID] = mapped_column(
        pg.UUID(), nullable=False, index=True
    )

    ext: Mapped[str] = mapped_column(sa.String(length=SMALL), nullable=False)

    moment: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=sa.text("timezone('utc', now())"),
    )


class KnownTags(Base):
    """User accessible cache of known tags.

    Requires:
        CREATE EXTENSION pg_trgm;
        CREATE EXTENSION btree_gin;
    """

    __tablename__ = 'known_tags'

    # primary and foreign keys ------------------------------------------------

    user_uuid: Mapped[UUID] = mapped_column(
        pg.UUID(),
        sa.ForeignKey('users.uuid', ondelete='CASCADE'),
        index=True,
        primary_key=True,
    )
    tag: Mapped[str] = mapped_column(
        sa.String(length=MEDIUM), nullable=False, index=True, primary_key=True
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
        sa.String(length=MEDIUM),
        unique=True,
        nullable=False,
        index=True,
        primary_key=True,
    )

    # fields ------------------------------------------------------------------

    counter: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    __table_args__ = (
        sa.Index(
            'ix_known_tags_anon',
            tag,
            postgresql_ops={'tag': 'text_pattern_ops'},
        ),
    )


class LongJob(Base):
    """Long mutation operations."""

    __tablename__ = 'long_jobs'

    # primary and foreign keys ------------------------------------------------

    id: Mapped[int] = mapped_column(
        sa.BigInteger,
        autoincrement=True,
        nullable=False,
        index=True,
        primary_key=True,
    )

    # fields ------------------------------------------------------------------

    name: Mapped[str] = mapped_column(sa.String(length=SMALL), nullable=False)

    user_uuid: Mapped[UUID] = mapped_column(
        pg.UUID(),
        sa.ForeignKey('users.uuid', ondelete='CASCADE'),
        index=True,
        primary_key=True,
    )

    target_uuid: Mapped[UUID | None] = mapped_column(
        pg.UUID(),
        sa.ForeignKey(
            'items.uuid',
            ondelete='CASCADE',
        ),
        nullable=True,
        index=True,
    )

    added: Mapped[list[str]] = mapped_column(pg.ARRAY(sa.Text), nullable=False)
    deleted: Mapped[list[str]] = mapped_column(
        pg.ARRAY(sa.Text), nullable=False
    )
    status: Mapped[str] = mapped_column(
        sa.String(length=SMALL), index=True, nullable=False
    )
    started: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=sa.text("timezone('utc', now())"),
    )
    duration: Mapped[float] = mapped_column(sa.Float, nullable=True)

    operations: Mapped[int] = mapped_column(sa.Integer, nullable=True)
    extras: Mapped[dict[str, Any]] = mapped_column(pg.JSONB, nullable=False)
    error: Mapped[str] = mapped_column(sa.Text, nullable=False)


class Item(Base):
    """Single unit of storage."""

    __tablename__ = 'items'

    # primary and foreign keys ------------------------------------------------

    id: Mapped[int] = mapped_column(
        sa.BigInteger,
        # TODO - actually make it a primary key
        # primary_key=True,  noqa: ERA001
        autoincrement=True,
        nullable=False,
        index=True,
        unique=True,
    )

    uuid: Mapped[UUID] = mapped_column(
        # TODO - remove from primary keys
        pg.UUID(),
        primary_key=True,
        nullable=False,
        index=True,
        unique=True,
    )

    parent_uuid: Mapped[UUID | None] = mapped_column(
        pg.UUID(),
        sa.ForeignKey(
            'items.uuid',
            ondelete='CASCADE',
        ),
        nullable=True,
        index=True,
    )

    owner_uuid: Mapped[UUID] = mapped_column(
        pg.UUID(),
        sa.ForeignKey(
            'users.uuid',
            ondelete='CASCADE',
        ),
        nullable=False,
        index=True,
    )

    # fields ------------------------------------------------------------------

    number: Mapped[int] = mapped_column(
        sa.BigInteger, autoincrement=True, nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(length=MEDIUM), nullable=False)
    is_collection: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    content_ext: Mapped[str | None] = mapped_column(
        sa.String(length=SMALL), nullable=True
    )
    preview_ext: Mapped[str | None] = mapped_column(
        sa.String(length=SMALL), nullable=True
    )
    thumbnail_ext: Mapped[str | None] = mapped_column(
        sa.String(length=SMALL), nullable=True
    )

    # array fields ------------------------------------------------------------

    tags: Mapped[list[str]] = mapped_column(pg.ARRAY(sa.Text), nullable=False)
    permissions: Mapped[list[str]] = mapped_column(
        pg.ARRAY(sa.Text), nullable=False
    )

    # methods -----------------------------------------------------------------

    def __repr__(self) -> str:
        """Return string representation."""
        return f'<DB Item, {self.uuid}, {self.name!r}>'

    # relations ---------------------------------------------------------------

    owner: Mapped[User] = relationship(
        'User',
        passive_deletes=True,
        back_populates='items',
        primaryjoin='Item.owner_uuid==User.uuid',
        uselist=False,
    )

    metainfo: Mapped['Metainfo'] = relationship(
        'Metainfo', passive_deletes=True, back_populates='item', uselist=False
    )

    media: Mapped['Media'] = relationship(
        'Media', passive_deletes=True, back_populates='item', uselist=True
    )

    exif: Mapped['EXIF'] = relationship(
        'EXIF', passive_deletes=True, back_populates='item', uselist=True
    )

    # other -------------------------------------------------------------------

    __table_args__ = (
        sa.Index('ix_items_tags', tags, postgresql_using='gin'),
        sa.Index('ix_items_permissions', permissions, postgresql_using='gin'),
    )


class Metainfo(Base):
    """Meta information for items."""

    __tablename__ = 'metainfo'

    # primary and foreign keys ------------------------------------------------

    item_uuid: Mapped[UUID] = mapped_column(
        pg.UUID(),
        sa.ForeignKey('items.uuid', ondelete='CASCADE'),
        nullable=False,
        index=True,
        primary_key=True,
    )

    # fields ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    user_time: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=False), nullable=True
    )

    content_type: Mapped[str] = mapped_column(
        sa.String(length=SMALL), nullable=True
    )

    extras: Mapped[dict[str, Any]] = mapped_column(pg.JSONB, nullable=False)

    content_size: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    preview_size: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    thumbnail_size: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True
    )

    content_width: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True
    )
    content_height: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True
    )
    preview_width: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True
    )
    preview_height: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True
    )
    thumbnail_width: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True
    )
    thumbnail_height: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True
    )

    # methods -----------------------------------------------------------------

    def __repr__(self) -> str:
        """Return string representation."""
        return f'<DB Metainfo, {self.item_uuid}, {self.content_type!r}>'

    # relations ---------------------------------------------------------------

    item: Mapped[Item] = relationship(
        'Item', passive_deletes=True, back_populates='metainfo', uselist=False
    )


class Media(Base):
    """Converted content from user.

    Fully processed user content. If it's an image then it's already converted
    to a desired size. At this point we're using database as a storage. Worker
    process must perform download job and save data to actual storage device.
    """

    __tablename__ = 'media'

    # primary and foreign keys ------------------------------------------------

    id: Mapped[int] = mapped_column(
        sa.BigInteger,
        autoincrement=True,
        nullable=False,
        index=True,
        primary_key=True,
    )

    # fields ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, index=True
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, index=True
    )
    error: Mapped[str] = mapped_column(sa.Text, nullable=True)

    owner_uuid: Mapped[UUID] = mapped_column(
        pg.UUID(),
        sa.ForeignKey('users.uuid', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    item_uuid: Mapped[UUID] = mapped_column(
        pg.UUID(),
        sa.ForeignKey('items.uuid', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    media_type: Mapped[str] = mapped_column(
        sa.Enum(
            const.CONTENT, const.PREVIEW, const.THUMBNAIL, name='media_type'
        ),
        nullable=False,
    )

    content: Mapped[bytes] = mapped_column(pg.BYTEA, nullable=False)
    ext: Mapped[str] = mapped_column(sa.String(length=SMALL), nullable=False)

    # relations ---------------------------------------------------------------

    owner: Mapped[User] = relationship(
        'User',
        passive_deletes=True,
        back_populates='media',
        primaryjoin='Media.owner_uuid==User.uuid',
        uselist=False,
    )

    item: Mapped[Item] = relationship(
        'Item', passive_deletes=True, back_populates='media', uselist=False
    )


class CommandCopy(Base):
    """Operation of copying image from one item to another."""

    __tablename__ = 'commands_copy'

    # primary and foreign keys ------------------------------------------------

    id: Mapped[int] = mapped_column(
        sa.BigInteger,
        autoincrement=True,
        nullable=False,
        index=True,
        primary_key=True,
    )

    # fields ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, index=True
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    error: Mapped[str] = mapped_column(sa.Text, nullable=True)

    owner_uuid: Mapped[UUID] = mapped_column(
        pg.UUID(),
        sa.ForeignKey('users.uuid', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    source_uuid: Mapped[UUID] = mapped_column(
        pg.UUID(),
        sa.ForeignKey(
            'items.uuid',
            ondelete='CASCADE',
        ),
        nullable=False,
    )

    target_uuid: Mapped[UUID] = mapped_column(
        pg.UUID(),
        sa.ForeignKey(
            'items.uuid',
            ondelete='CASCADE',
        ),
        nullable=False,
    )

    media_type: Mapped[str] = mapped_column(
        sa.Enum(
            const.CONTENT, const.PREVIEW, const.THUMBNAIL, name='media_type'
        ),
        nullable=False,
    )

    ext: Mapped[str] = mapped_column(sa.String(length=SMALL), nullable=False)


class EXIF(Base):
    """EXIF information for items."""

    __tablename__ = 'exif'

    # primary and foreign keys ------------------------------------------------

    item_uuid: Mapped[UUID] = mapped_column(
        pg.UUID(),
        sa.ForeignKey('items.uuid', ondelete='CASCADE'),
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
        sa.BigInteger,
        sa.ForeignKey('items.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        unique=True,
        primary_key=True,
    )

    # fields ------------------------------------------------------------------

    signature: Mapped[str] = mapped_column(
        sa.CHAR(32), nullable=False, index=True
    )


class SignatureCRC32(Base):
    """CRC32 hash for item content."""

    __tablename__ = 'signatures_crc32'

    # primary and foreign keys ------------------------------------------------

    item_id: Mapped[int] = mapped_column(
        sa.BigInteger,
        sa.ForeignKey('items.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        unique=True,
        primary_key=True,
    )

    # fields ------------------------------------------------------------------

    signature: Mapped[int] = mapped_column(
        sa.BigInteger, nullable=False, index=True
    )


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
    )

    # fields ------------------------------------------------------------------

    worker_name: Mapped[str] = mapped_column(
        sa.CHAR(MEDIUM), nullable=False, index=True, unique=True
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
    )

    # fields ------------------------------------------------------------------

    worker_name: Mapped[str] = mapped_column(sa.VARCHAR(MEDIUM), nullable=True)

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
    )

    # fields ------------------------------------------------------------------

    name: Mapped[str] = mapped_column(sa.VARCHAR(MEDIUM), nullable=False)
    worker_name: Mapped[str] = mapped_column(sa.VARCHAR(MEDIUM), nullable=True)

    status: Mapped[str] = mapped_column(
        sa.Enum(
            'created',
            'processing',
            'done',
            'failed',
            name='serial_operation_status',
        )
    )

    extras: Mapped[dict[str, Any]] = mapped_column(pg.JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    log: Mapped[str] = mapped_column(sa.Text, nullable=True)


if __name__ == '__main__':
    db_url = os.environ[const.ENV_DB_URL_ADMIN]
    engine = sa.create_engine(db_url, echo=True)
    metadata.create_all(engine, checkfirst=True)
