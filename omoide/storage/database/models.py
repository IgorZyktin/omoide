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
    visibility = sa.Column(sa.String(length=MEDIUM), nullable=True)
    language = sa.Column(sa.String(length=SMALL), nullable=True)
    last_seen = sa.Column(sa.DateTime(timezone=True), nullable=True)

    # relations ---------------------------------------------------------------

    groups = relationship('Group',
                          back_populates='owner',
                          order_by='Group.name')
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


class Visibility(Base):
    """Chosen set of items to display."""
    __tablename__ = 'visibility'

    # primary and foreign keys ------------------------------------------------

    owner_uuid = sa.Column(pg.UUID,
                           sa.ForeignKey('users.uuid'),
                           nullable=False,
                           index=True,
                           primary_key=True)

    name = sa.Column(sa.String(length=MEDIUM),
                     primary_key=True,
                     nullable=False,
                     index=True)

    # array fields ------------------------------------------------------------

    anchors = sa.Column(pg.ARRAY(sa.Text), nullable=False)

    # fields ------------------------------------------------------------------

    stats = sa.Column(sa.JSON, nullable=False)
    # TODO - probably should add tags here


class Group(Base):
    """Personal collection of users."""
    __tablename__ = 'groups'

    # primary and foreign keys ------------------------------------------------

    owner_uuid = sa.Column(pg.UUID,
                           sa.ForeignKey('users.uuid'),
                           nullable=False,
                           index=True,
                           primary_key=True)

    name = sa.Column(sa.String(length=MEDIUM),
                     primary_key=True,
                     nullable=False,
                     index=True)

    # array fields ------------------------------------------------------------

    users = sa.Column(pg.ARRAY(sa.Text), nullable=False)

    # relations ---------------------------------------------------------------

    owner = relationship('User', back_populates='groups')

    # other -------------------------------------------------------------------

    sa.UniqueConstraint('owner_uuid', 'name', name='uix_group_name_and_owner')


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
    stats = relationship('Stats', back_populates='item')
    meta = relationship('Meta', back_populates='item')
    exif = relationship('Exif', back_populates='item')
    media = relationship('Media', back_populates='item')

    # other -------------------------------------------------------------------

    __table_args__ = (
        sa.Index('ix_image_tags', tags, postgresql_using='gin'),
        sa.Index('ix_image_permissions', permissions, postgresql_using='gin'),
    )


class ComputedTags(Base):
    """Combined tags of whole hierarchy of items."""
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
    """Combined permissions of whole hierarchy of items."""
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


# TODO - probably should get rid of this class
class Stats(Base):
    """Statistic for whole branch of items."""
    __tablename__ = 'stats'

    # primary and foreign keys ------------------------------------------------

    item_uuid = sa.Column(pg.UUID,
                          sa.ForeignKey('items.uuid'),
                          nullable=False,
                          index=True,
                          primary_key=True)

    # fields ------------------------------------------------------------------

    data = sa.Column(sa.JSON, nullable=False)

    # relations ---------------------------------------------------------------

    item = relationship('Item', back_populates='stats')


class Exif(Base):
    """Exif information for images."""
    __tablename__ = 'exif'

    # primary and foreign keys ------------------------------------------------

    item_uuid = sa.Column(pg.UUID,
                          sa.ForeignKey('items.uuid'),
                          nullable=False,
                          index=True,
                          primary_key=True)

    # fields ------------------------------------------------------------------

    data = sa.Column(sa.JSON, nullable=False)

    # relations ---------------------------------------------------------------

    item = relationship('Item', back_populates='exif')


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


class Media(Base):
    """Temporary storage for unsaved media data."""
    __tablename__ = 'media'

    # primary and foreign keys ------------------------------------------------

    item_uuid = sa.Column(pg.UUID,
                          sa.ForeignKey('items.uuid'),
                          nullable=False,
                          index=True,
                          primary_key=True)

    # fields ------------------------------------------------------------------

    content = sa.Column(pg.BYTEA, nullable=True)
    preview = sa.Column(pg.BYTEA, nullable=True)
    thumbnail = sa.Column(pg.BYTEA, nullable=True)
    added_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    saved_at = sa.Column(sa.DateTime(timezone=True), nullable=True)

    # relations ---------------------------------------------------------------

    item = relationship('Item', back_populates='media')
