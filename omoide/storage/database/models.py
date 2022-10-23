# -*- coding: utf-8 -*-
"""Database implementation of the domain.

PostgreSQL specific because application needs arrays.
"""
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

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
    root_item: Optional[UUID] = sa.Column(pg.UUID(),
                                          sa.ForeignKey('items.uuid',
                                                        ondelete='SET NULL'),
                                          nullable=True,
                                          index=True)
    # relations ---------------------------------------------------------------

    items: list['Item'] = relationship('Item',
                                       passive_deletes=True,
                                       primaryjoin=(
                                           'Item.owner_uuid==User.uuid'
                                       ),
                                       back_populates='owner',
                                       uselist=True)

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


class Item(Base):
    """Single unit of storage."""
    __tablename__ = 'items'

    # primary and foreign keys ------------------------------------------------

    uuid: UUID = sa.Column(pg.UUID(),
                           primary_key=True,
                           nullable=False,
                           index=True,
                           unique=True)

    parent_uuid: Optional[UUID] = sa.Column(pg.UUID(),
                                            sa.ForeignKey('items.uuid',
                                                          ondelete='CASCADE'),
                                            nullable=True,
                                            index=True)

    owner_uuid: UUID = sa.Column(pg.UUID(),
                                 sa.ForeignKey('users.uuid',
                                               ondelete='CASCADE'),
                                 nullable=False,
                                 index=True)

    number = sa.Column(sa.BigInteger, nullable=False)

    # fields ------------------------------------------------------------------

    name = sa.Column(sa.String(length=MEDIUM), nullable=False)
    is_collection = sa.Column(sa.Boolean, nullable=False)
    content_ext = sa.Column(sa.String(length=SMALL), nullable=True)
    preview_ext = sa.Column(sa.String(length=SMALL), nullable=True)
    thumbnail_ext = sa.Column(sa.String(length=SMALL), nullable=True)

    # array fields ------------------------------------------------------------

    tags = sa.Column(pg.ARRAY(sa.Text), nullable=False)
    permissions = sa.Column(pg.ARRAY(sa.Text), nullable=False)

    # relations ---------------------------------------------------------------

    owner: User = relationship('User',
                               passive_deletes=True,
                               back_populates='items',
                               primaryjoin='Item.owner_uuid==User.uuid',
                               uselist=False)

    meta: 'Meta' = relationship('Meta',
                                passive_deletes=True,
                                back_populates='item',
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
        sa.Index('ix_image_tags', tags, postgresql_using='gin'),
        sa.Index('ix_image_permissions', permissions, postgresql_using='gin'),
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


class ComputedPermissions(Base):
    """Combined permissions of whole hierarchy of items.

    No inheritance involved, permissions are separate for each record.

    Records:
        item1 with permissions {'family', 'friends'}
        item2 with permissions {'colleagues'}

    Computed permissions example:
        item1 with permissions {'user_uuid1', 'user_uuid2', 'user_uuid3'}
        item2 with permissions {'user_uuid3', 'user_uuid4'}
    """
    __tablename__ = 'computed_permissions'

    # primary and foreign keys ------------------------------------------------

    item_uuid: UUID = sa.Column(pg.UUID(),
                                sa.ForeignKey('items.uuid',
                                              ondelete='CASCADE'),
                                primary_key=True,
                                nullable=False,
                                index=True,
                                unique=True)

    # array fields ------------------------------------------------------------

    permissions = sa.Column(pg.ARRAY(sa.Text), nullable=False)

    # other -------------------------------------------------------------------

    __table_args__ = (
        sa.Index('ix_computed_permissions',
                 permissions,
                 postgresql_using='gin'),
    )


# TODO: drop this table, it's useless
class Meta(Base):
    """Meta information for items."""
    __tablename__ = 'meta'

    # primary and foreign keys ------------------------------------------------

    item_uuid: UUID = sa.Column(pg.UUID(),
                                sa.ForeignKey('items.uuid',
                                              ondelete='CASCADE'),
                                nullable=False,
                                index=True,
                                primary_key=True)

    # fields ------------------------------------------------------------------

    data = sa.Column(pg.JSONB, nullable=False)

    # relations ---------------------------------------------------------------

    item: Item = relationship('Item',
                              passive_deletes=True,
                              back_populates='meta',
                              uselist=False)


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

    created_at = sa.Column(sa.DateTime(timezone=True),
                           nullable=False)
    updated_at = sa.Column(sa.DateTime(timezone=True),
                           nullable=False)
    deleted_at = sa.Column(sa.DateTime(timezone=True),
                           nullable=True)
    user_time = sa.Column(sa.DateTime(timezone=False),
                          nullable=True)

    width = sa.Column(sa.Integer, nullable=True)
    height = sa.Column(sa.Integer, nullable=True)
    duration = sa.Column(sa.Float, nullable=True)
    resolution = sa.Column(sa.Float, nullable=True)
    size = sa.Column(sa.Integer, nullable=True)
    media_type = sa.Column(sa.String(length=SMALL), nullable=True)

    author = sa.Column(sa.String(length=MEDIUM), nullable=True)
    author_url = sa.Column(sa.String(length=HUGE), nullable=True)
    saved_from_url = sa.Column(sa.String(length=HUGE), nullable=True)
    description = sa.Column(sa.String(length=HUGE), nullable=True)

    extras = sa.Column(pg.JSONB, nullable=False)

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
    # TODO(i.zyktin): Theoretically, we can serve content directly from
    #  the database during time before download job completes. This way it
    #  will be 50x times slower than from the filesystem but could give better
    #  user experience. Especially if download job will launch rarely
    #  (like every 30 minutes or so).
    __tablename__ = 'media'

    # primary and foreign keys ------------------------------------------------

    item_uuid: UUID = sa.Column(pg.UUID(),
                                sa.ForeignKey('items.uuid',
                                              ondelete='CASCADE'),
                                primary_key=True,
                                nullable=False,
                                index=True)
    media_type = sa.Column(sa.Enum('content',
                                   'preview',
                                   'thumbnail',
                                   name='media_type'),
                           primary_key=True)

    # fields ------------------------------------------------------------------

    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    processed_at = sa.Column(sa.DateTime(timezone=True), nullable=True)
    status = sa.Column(sa.Enum('init', 'work', 'done', 'fail', name='status'),
                       index=True)
    content = sa.Column(pg.BYTEA, nullable=False)
    ext = sa.Column(sa.String(length=SMALL), nullable=False)

    # relations ---------------------------------------------------------------

    item: Item = relationship('Item',
                              passive_deletes=True,
                              back_populates='media',
                              uselist=False)

    # other -------------------------------------------------------------------

    __table_args__ = (
        sa.UniqueConstraint('item_uuid', 'media_type', name='uix_media'),
    )


# Feature: Add table for signatures. This will allow us to distinguish same
# bad payloads and search for duplicates. Someday we could put ImageMatch here.
# Possible structure:
# class Signature(Base):
#   item_uuid: ...
#   md5: ...


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

    exif = sa.Column(pg.JSONB, nullable=False)

    # relations ---------------------------------------------------------------

    item: Item = relationship('Item',
                              passive_deletes=True,
                              back_populates='exif',
                              uselist=False)


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

    media_type = sa.Column(sa.Enum('content',
                                   'preview',
                                   'thumbnail',
                                   name='media_type'))

    owner_uuid: UUID = sa.Column(pg.UUID(),
                                 nullable=False,
                                 index=True)

    item_uuid: UUID = sa.Column(pg.UUID(),
                                nullable=False,
                                index=True)

    ext = sa.Column(sa.String(length=SMALL), nullable=False)

    moment = sa.Column(sa.DateTime(timezone=True),
                       nullable=False,
                       index=True,
                       server_default=sa.text("timezone('utc', now())"))


class FilesystemOperation(Base):
    """Operations that have to be executed on filesystem."""
    __tablename__ = 'filesystem_operations'

    # primary and foreign keys ------------------------------------------------

    id: int = sa.Column(sa.BigInteger,
                        autoincrement=True,
                        nullable=False,
                        index=True,
                        primary_key=True)

    # fields ------------------------------------------------------------------
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    processed_at = sa.Column(sa.DateTime(timezone=True), nullable=True)
    status = sa.Column(sa.String(length=SMALL), index=True, nullable=False)
    error = sa.Column(sa.Text)

    source_uuid: UUID = sa.Column(pg.UUID(), nullable=False)
    target_uuid: UUID = sa.Column(pg.UUID(), nullable=False)

    operation = sa.Column(sa.String(length=MEDIUM), nullable=False)
    extras = sa.Column(pg.JSON, nullable=False)
