# -*- coding: utf-8 -*-
"""Database implementation of the domain.

PostgreSQL specific because application needs arrays.
"""
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import declarative_base, relationship

metadata = sa.MetaData()
Base = declarative_base(metadata=metadata)

HUGE = 1024
MEDIUM = 256
SMALL = 64


class User(Base):
    """User model."""
    __tablename__ = 'users'

    # primary and foreign keys ------------------------------------------------

    uuid: UUID = sa.Column(pg.UUID(as_uuid=True),
                           primary_key=True,
                           nullable=False,
                           index=True,
                           unique=True)

    # fields ------------------------------------------------------------------

    login = sa.Column(sa.String(length=MEDIUM), nullable=False, unique=True)
    password = sa.Column(sa.String(length=HUGE), nullable=False)
    name = sa.Column(sa.String(length=MEDIUM), nullable=False)
    root_item: Optional[UUID] = sa.Column(pg.UUID(as_uuid=True),
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

    user_uuid: UUID = sa.Column(pg.UUID(as_uuid=True),
                                sa.ForeignKey('users.uuid',
                                              ondelete='CASCADE'),
                                nullable=False,
                                index=True,
                                unique=True)


class Item(Base):
    """Single unit of storage."""
    __tablename__ = 'items'

    # primary and foreign keys ------------------------------------------------

    uuid: UUID = sa.Column(pg.UUID(as_uuid=True),
                           primary_key=True,
                           nullable=False,
                           index=True,
                           unique=True)

    parent_uuid: Optional[UUID] = sa.Column(pg.UUID(as_uuid=True),
                                            sa.ForeignKey('items.uuid',
                                                          ondelete='CASCADE'),
                                            nullable=True,
                                            index=True)

    owner_uuid: UUID = sa.Column(pg.UUID(as_uuid=True),
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
    raw_media: 'RawMedia' = relationship('RawMedia',
                                         passive_deletes=True,
                                         back_populates='item',
                                         uselist=False)
    media: 'Media' = relationship('Media',
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

    item_uuid: UUID = sa.Column(pg.UUID(as_uuid=True),
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

    item_uuid: UUID = sa.Column(pg.UUID(as_uuid=True),
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


class Meta(Base):
    """Meta information for items."""
    __tablename__ = 'meta'

    # primary and foreign keys ------------------------------------------------

    item_uuid: UUID = sa.Column(pg.UUID(as_uuid=True),
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

    # Feature: drop this table, it's useless


# Feature: make new Metainfo table with specific fields.
# Possible structure:
# class Meta(Base):
#   item_uuid: ...
#   --- automatic ---
#   width: ...
#   height: ...
#   duration: ...
#   resolution: ...
#   size: ...
#   \type: ...
#   added_at: ...
#   updated_at: ...
#   --- manual ---
#   author: ...
#   author_url: ...
#   saved_from_url: ...
#   description: ...


# Feature: Create Exif table and store there exif tags for images
# Possible structure:
# class Meta(Base):
#   item_uuid: ...
#   data = ...


class RawMedia(Base):
    """Initial content from user, not processed at all.

    Content is not trustworthy, must be handled carefully.
    At this moment we only got some bytes from user and know the filename.
    Maybe there is a zip bomb inside. Also note that content is not loaded yet,
    but the item is already exist (and can be seen with empty thumbnail).
    """
    __tablename__ = 'raw_media'

    # primary and foreign keys ------------------------------------------------

    id = sa.Column(sa.BigInteger,
                   primary_key=True,
                   autoincrement=True,
                   nullable=False)

    item_uuid: UUID = sa.Column(pg.UUID(as_uuid=True),
                                sa.ForeignKey('items.uuid',
                                              ondelete='CASCADE'),
                                nullable=False,
                                index=True)

    # fields ------------------------------------------------------------------

    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    processed_at = sa.Column(sa.DateTime(timezone=True), nullable=True)
    status = sa.Column(sa.Enum('init', 'work', 'done', 'fail', name='status'),
                       index=True)
    filename = sa.Column(sa.String(length=MEDIUM), nullable=False)
    content = sa.Column(pg.BYTEA, nullable=False)
    features = sa.Column(pg.ARRAY(sa.Text), nullable=False)
    attempts = sa.Column(sa.Integer, nullable=False, server_default='0')

    # relations ---------------------------------------------------------------

    item: Item = relationship('Item',
                              passive_deletes=True,
                              back_populates='raw_media',
                              uselist=False)

    # Feature: Add 'attempts' field in case if we could not handle media in
    # adequate amount of attempts. Also tie this table to the Signatures table,
    # in case if nasty user will try to load something like zip-bomb again
    # and again. Without this measure user theoretically could take down c
    # luster of workers of any size since workers will die on zip-bomb one
    # by one repeatedly.


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

    item_uuid: UUID = sa.Column(pg.UUID(as_uuid=True),
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
