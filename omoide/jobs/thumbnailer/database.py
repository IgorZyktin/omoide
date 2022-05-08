# -*- coding: utf-8 -*-
"""Database operations for thumbnailer job.
"""
from typing import Optional

from sqlalchemy.orm import Session

from omoide.storage.database.models import Item


def get_items_without_thumbnail(session: Session) -> list[Item]:
    """Return some media records to save."""
    return session.query(Item).where(
        Item.thumbnail_ext == None).all()  # noqa: E711


def get_first_child(session: Session, item: Item) -> Optional[Item]:
    """Get first child with thumbnail for given item."""
    child = session.query(Item).where(
        Item.parent_uuid == item.uuid
    ).order_by(Item.number).first()

    if child is None:
        return None

    if child.thumbnail_ext is None:
        # maybe it has own children with thumbnail
        return get_first_child(session, child)

    return child
