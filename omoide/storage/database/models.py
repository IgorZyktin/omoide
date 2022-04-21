# -*- coding: utf-8 -*-
"""Database implementation of the domain.

PostgreSQL specific because application needs arrays.
"""
import uuid

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

    uuid = sa.Column(pg.UUID,
                     primary_key=True,
                     nullable=False,
                     index=True,
                     default=uuid.uuid4,
                     unique=True)

    # fields ------------------------------------------------------------------

    login = sa.Column(sa.String(length=MEDIUM), nullable=False, unique=True)
    password = sa.Column(sa.String(length=HUGE), nullable=False)
    name = sa.Column(sa.String(length=MEDIUM), nullable=False)

    # relations ---------------------------------------------------------------

    items = relationship('Item', back_populates='owner')


class PublicUsers(Base):
    """List of users who demonstrate their content publicly."""
    __tablename__ = 'public_users'

    # primary and foreign keys ------------------------------------------------
    number = sa.Column(sa.Integer,
                       autoincrement=True,
                       nullable=False,
                       primary_key=True)

    user_uuid = sa.Column(pg.UUID,
                          sa.ForeignKey('users.uuid'),
                          nullable=False,
                          index=True,
                          unique=True)


class Item(Base):
    """Single unit of storage."""
    __tablename__ = 'items'

    # primary and foreign keys ------------------------------------------------

    uuid = sa.Column(pg.UUID,
                     primary_key=True,
                     nullable=False,
                     index=True,
                     default=uuid.uuid4,
                     unique=True)

    parent_uuid = sa.Column(pg.UUID,
                            sa.ForeignKey('items.uuid'),
                            nullable=True,
                            index=True)

    owner_uuid = sa.Column(pg.UUID,
                           sa.ForeignKey('users.uuid'),
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

    owner = relationship('User', back_populates='items')

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

    item_uuid = sa.Column(pg.UUID,
                          sa.ForeignKey('items.uuid'),
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

    item_uuid = sa.Column(pg.UUID,
                          sa.ForeignKey('items.uuid'),
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

    item_uuid = sa.Column(pg.UUID,
                          sa.ForeignKey('items.uuid'),
                          nullable=False,
                          index=True,
                          primary_key=True)

    # fields ------------------------------------------------------------------

    data = sa.Column(pg.JSONB, nullable=False)

    # relations ---------------------------------------------------------------

    item = relationship('Item', back_populates='meta')


class RawMedia(Base):
    """Initial content from user, not processed at all."""
    __tablename__ = 'raw_media'

    # primary and foreign keys ------------------------------------------------

    id = sa.Column(sa.BigInteger,
                   primary_key=True,
                   autoincrement=True,
                   nullable=False)
    item_uuid = sa.Column(pg.UUID,
                          sa.ForeignKey('items.uuid'),
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

    # relations ---------------------------------------------------------------

    item = relationship('Item', back_populates='raw_media')
