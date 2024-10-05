"""Database implementation of the domain.

PostgreSQL specific because application needs arrays.
"""
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

from omoide import const

metadata = sa.MetaData()
Base = declarative_base(metadata=metadata)

HUGE = 1024
MEDIUM = 256
SMALL = 64


class User(Base):
    """User model."""
    __tablename__ = 'users'

    # primary and foreign keys ------------------------------------------------

    uuid: UUID = sa.Column(pg.UUID(),
                           primary_key=True,
                           nullable=False,
                           index=True,
                           unique=True)

    # fields ------------------------------------------------------------------

    login = sa.Column(sa.String(length=MEDIUM), nullable=False, unique=True)
    password = sa.Column(sa.String(length=HUGE), nullable=False)
    name = sa.Column(sa.String(length=MEDIUM), nullable=False)
    auth_complexity = sa.Column(sa.Integer, nullable=False)

    # relations ---------------------------------------------------------------

    items: list['Item'] = relationship('Item',
                                       passive_deletes=True,
                                       primaryjoin=(
                                           'Item.owner_uuid==User.uuid'
                                       ),
                                       back_populates='owner',
                                       uselist=True)

    media: 'Media' = relationship('Media',
                                  passive_deletes=True,
                                  primaryjoin=(
                                      'Media.owner_uuid==User.uuid'
                                  ),
                                  back_populates='owner',
                                  uselist=True)

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

    # Feature: Add field is_admin to be able to create superusers


class PublicUsers(Base):
    """List of users who demonstrate their content publicly."""
    __tablename__ = 'public_users'

    # primary and foreign keys ------------------------------------------------
    number = sa.Column(sa.Integer,
                       autoincrement=True,
                       nullable=False,
                       primary_key=True)

    user_uuid: UUID = sa.Column(pg.UUID(),
                                sa.ForeignKey('users.uuid',
                                              ondelete='CASCADE'),
                                nullable=False,
                                index=True,
                                unique=True)


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

    item_uuid: UUID = sa.Column(pg.UUID(),
                                sa.ForeignKey('items.uuid',
                                              ondelete='CASCADE'),
                                primary_key=True,
                                nullable=False,
                                index=True,
                                unique=True)

    # array fields ------------------------------------------------------------

    tags = sa.Column(pg.ARRAY(sa.Text), nullable=False)

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

    id: int = sa.Column(sa.BigInteger,
                        autoincrement=True,
                        nullable=False,
                        index=True,
                        primary_key=True)

    # fields ------------------------------------------------------------------

    media_type: str = sa.Column(sa.Enum(const.CONTENT,
                                        const.PREVIEW,
                                        const.THUMBNAIL,
                                        name='media_type'))

    owner_uuid: UUID = sa.Column(pg.UUID(),
                                 nullable=False,
                                 index=True)

    item_uuid: UUID = sa.Column(pg.UUID(),
                                nullable=False,
                                index=True)

    ext: str = sa.Column(sa.String(length=SMALL), nullable=False)

    moment: datetime = sa.Column(sa.DateTime(timezone=True),
                                 nullable=False,
                                 index=True,
                                 server_default=sa.text(
                                     "timezone('utc', now())"))


class KnownTags(Base):
    """User accessible cache of known tags.

    Requires:
        CREATE EXTENSION pg_trgm;
        CREATE EXTENSION btree_gin;
    """
    __tablename__ = 'known_tags'

    # primary and foreign keys ------------------------------------------------

    user_uuid: UUID = sa.Column(pg.UUID(),
                                sa.ForeignKey('users.uuid',
                                              ondelete='CASCADE'),
                                index=True,
                                primary_key=True)
    tag: str = sa.Column(sa.String(length=MEDIUM),
                         nullable=False,
                         index=True,
                         primary_key=True)

    # fields ------------------------------------------------------------------

    counter: int = sa.Column(sa.Integer, nullable=False)

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

    tag: str = sa.Column(sa.String(length=MEDIUM),
                         unique=True,
                         nullable=False,
                         index=True,
                         primary_key=True)

    # fields ------------------------------------------------------------------

    counter: int = sa.Column(sa.Integer, nullable=False)

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

    id: int = sa.Column(sa.BigInteger,
                        autoincrement=True,
                        nullable=False,
                        index=True,
                        primary_key=True)

    # fields ------------------------------------------------------------------

    name: str = sa.Column(sa.String(length=SMALL), nullable=False)

    user_uuid: UUID = sa.Column(pg.UUID(),
                                sa.ForeignKey('users.uuid',
                                              ondelete='CASCADE'),
                                index=True,
                                primary_key=True)

    target_uuid: UUID | None = sa.Column(pg.UUID(),
                                         sa.ForeignKey('items.uuid',
                                                       ondelete='CASCADE'),
                                         nullable=True,
                                         index=True)

    added = sa.Column(pg.ARRAY(sa.Text), nullable=False)
    deleted = sa.Column(pg.ARRAY(sa.Text), nullable=False)
    status: str = sa.Column(sa.String(length=SMALL),
                            index=True,
                            nullable=False)
    started: datetime = sa.Column(sa.DateTime(timezone=True),
                                  nullable=False,
                                  index=True,
                                  server_default=sa.text(
                                      "timezone('utc', now())"))
    duration: float = sa.Column(sa.Float, nullable=True)

    operations: int = sa.Column(sa.Integer, nullable=True)
    extras: dict = sa.Column(pg.JSONB, nullable=False)
    error: str = sa.Column(sa.Text, nullable=False)


class Item(Base):
    """Single unit of storage."""
    __tablename__ = 'items'

    # primary and foreign keys ------------------------------------------------

    id: int = sa.Column(sa.BigInteger,
                        # TODO - actually make it a primary key
                        # primary_key=True,
                        autoincrement=True,
                        nullable=False,
                        index=True,
                        unique=True)

    uuid: UUID = sa.Column(pg.UUID(),
                           primary_key=True,
                           nullable=False,
                           index=True,
                           unique=True)

    parent_uuid: UUID | None = sa.Column(pg.UUID(),
                                         sa.ForeignKey('items.uuid',
                                                       ondelete='CASCADE'),
                                         nullable=True,
                                         index=True)

    owner_uuid: UUID = sa.Column(pg.UUID(),
                                 sa.ForeignKey('users.uuid',
                                               ondelete='CASCADE'),
                                 nullable=False,
                                 index=True)

    # fields ------------------------------------------------------------------

    number = sa.Column(sa.BigInteger, autoincrement=True, nullable=False)
    name = sa.Column(sa.String(length=MEDIUM), nullable=False)
    is_collection = sa.Column(sa.Boolean, nullable=False)
    content_ext: str | None = sa.Column(sa.String(length=SMALL),
                                        nullable=True)
    preview_ext: str | None = sa.Column(sa.String(length=SMALL),
                                        nullable=True)
    thumbnail_ext: str | None = sa.Column(sa.String(length=SMALL),
                                          nullable=True)

    # array fields ------------------------------------------------------------

    tags = sa.Column(pg.ARRAY(sa.Text), nullable=False)
    permissions = sa.Column(pg.ARRAY(sa.Text), nullable=False)

    # methods -----------------------------------------------------------------

    def __repr__(self) -> str:
        """Return string representation."""
        return f'<DB Item, {self.uuid}, {self.name!r}>'

    # relations ---------------------------------------------------------------

    owner: User = relationship('User',
                               passive_deletes=True,
                               back_populates='items',
                               primaryjoin='Item.owner_uuid==User.uuid',
                               uselist=False)

    metainfo: 'Metainfo' = relationship('Metainfo',
                                        passive_deletes=True,
                                        back_populates='item',
                                        uselist=False)

    media: 'Media' = relationship('Media',
                                  passive_deletes=True,
                                  back_populates='item',
                                  uselist=True)

    exif: 'EXIF' = relationship('EXIF',
                                passive_deletes=True,
                                back_populates='item',
                                uselist=True)

    # other -------------------------------------------------------------------

    __table_args__ = (
        sa.Index('ix_items_tags', tags, postgresql_using='gin'),
        sa.Index('ix_items_permissions', permissions, postgresql_using='gin'),
    )


class Metainfo(Base):
    """Meta information for items."""
    __tablename__ = 'metainfo'

    # primary and foreign keys ------------------------------------------------

    item_uuid: UUID = sa.Column(pg.UUID(),
                                sa.ForeignKey('items.uuid',
                                              ondelete='CASCADE'),
                                nullable=False,
                                index=True,
                                primary_key=True)

    # fields ------------------------------------------------------------------

    created_at: datetime = sa.Column(sa.DateTime(timezone=True),
                                     nullable=False)
    updated_at: datetime = sa.Column(sa.DateTime(timezone=True),
                                     nullable=False)
    deleted_at: datetime | None = sa.Column(sa.DateTime(timezone=True),
                                            nullable=True)
    user_time: datetime | None = sa.Column(sa.DateTime(timezone=False),
                                           nullable=True)

    content_type = sa.Column(sa.String(length=SMALL), nullable=True)

    extras: dict = sa.Column(pg.JSONB, nullable=False)

    content_size: int | None = sa.Column(sa.Integer, nullable=True)
    preview_size: int | None = sa.Column(sa.Integer, nullable=True)
    thumbnail_size: int | None = sa.Column(sa.Integer, nullable=True)

    content_width: int | None = sa.Column(sa.Integer, nullable=True)
    content_height: int | None = sa.Column(sa.Integer, nullable=True)
    preview_width: int | None = sa.Column(sa.Integer, nullable=True)
    preview_height: int | None = sa.Column(sa.Integer, nullable=True)
    thumbnail_width: int | None = sa.Column(sa.Integer, nullable=True)
    thumbnail_height: int | None = sa.Column(sa.Integer, nullable=True)

    # methods -----------------------------------------------------------------

    def __repr__(self) -> str:
        """Return string representation."""
        return f'<DB Metainfo, {self.item_uuid}, {self.content_type!r}>'

    # relations ---------------------------------------------------------------

    item: Item = relationship('Item',
                              passive_deletes=True,
                              back_populates='metainfo',
                              uselist=False)


class Media(Base):
    """Converted content from user.

    Fully processed user content. If it's an image then it's already converted
    to a desired size. At this point we're using database as a storage. Worker
    process must perform download job and save data to actual storage device.
    """
    __tablename__ = 'media'

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
                                              nullable=True,
                                              index=True)
    error: str = sa.Column(sa.Text, nullable=True)

    owner_uuid: UUID = sa.Column(pg.UUID(),
                                 sa.ForeignKey('users.uuid',
                                               ondelete='CASCADE'),
                                 nullable=False,
                                 index=True)

    item_uuid: UUID = sa.Column(pg.UUID(),
                                sa.ForeignKey('items.uuid',
                                              ondelete='CASCADE'),
                                nullable=False,
                                index=True)

    media_type: str = sa.Column(sa.Enum(const.CONTENT,
                                        const.PREVIEW,
                                        const.THUMBNAIL,
                                        name='media_type'),
                                nullable=False)

    content: bytes = sa.Column(pg.BYTEA, nullable=False)
    ext: str = sa.Column(sa.String(length=SMALL), nullable=False)

    # relations ---------------------------------------------------------------

    owner: User = relationship('User',
                               passive_deletes=True,
                               back_populates='media',
                               primaryjoin='Media.owner_uuid==User.uuid',
                               uselist=False)

    item: Item = relationship('Item',
                              passive_deletes=True,
                              back_populates='media',
                              uselist=False)


class CommandCopy(Base):
    """Operation of copying image from one item to another."""
    __tablename__ = 'commands_copy'

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

    error: str = sa.Column(sa.Text, nullable=True)

    owner_uuid: UUID = sa.Column(pg.UUID(),
                                 sa.ForeignKey('users.uuid',
                                               ondelete='CASCADE'),
                                 nullable=False,
                                 index=True)

    source_uuid: UUID = sa.Column(pg.UUID(),
                                  sa.ForeignKey('items.uuid',
                                                ondelete='CASCADE'),
                                  nullable=False)

    target_uuid: UUID = sa.Column(pg.UUID(),
                                  sa.ForeignKey('items.uuid',
                                                ondelete='CASCADE'),
                                  nullable=False)

    media_type: str = sa.Column(sa.Enum(const.CONTENT,
                                        const.PREVIEW,
                                        const.THUMBNAIL,
                                        name='media_type'),
                                nullable=False)

    ext: str = sa.Column(sa.String(length=SMALL), nullable=False)


class EXIF(Base):
    """EXIF information for items."""
    __tablename__ = 'exif'

    # primary and foreign keys ------------------------------------------------

    item_uuid: UUID = sa.Column(pg.UUID(),
                                sa.ForeignKey('items.uuid',
                                              ondelete='CASCADE'),
                                nullable=False,
                                index=True,
                                primary_key=True)

    # fields ------------------------------------------------------------------

    exif: dict = sa.Column(pg.JSONB, nullable=False)

    # relations ---------------------------------------------------------------

    item: Item = relationship('Item',
                              passive_deletes=True,
                              back_populates='exif',
                              uselist=False)


class SignatureMD5(Base):
    """MD5 hash for item content."""
    __tablename__ = 'signatures_md5'

    # primary and foreign keys ------------------------------------------------

    item_id: int = sa.Column(sa.BigInteger,
                             sa.ForeignKey('items.id', ondelete='CASCADE'),
                             nullable=False,
                             index=True,
                             unique=True,
                             primary_key=True)

    # fields ------------------------------------------------------------------

    signature: str = sa.Column(sa.CHAR(32), nullable=False)


class SignatureCRC32(Base):
    """CRC32 hash for item content."""
    __tablename__ = 'signatures_crc32'

    # primary and foreign keys ------------------------------------------------

    item_id: int = sa.Column(sa.BigInteger,
                             sa.ForeignKey('items.id', ondelete='CASCADE'),
                             nullable=False,
                             index=True,
                             unique=True,
                             primary_key=True)

    # fields ------------------------------------------------------------------

    signature: int = sa.Column(sa.BigInteger, nullable=False)
