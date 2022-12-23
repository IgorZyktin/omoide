# -*- coding: utf-8 -*-
"""Common database queries.
"""
import sqlalchemy as sa
from sqlalchemy.sql import Select

from omoide import domain
from omoide.storage.database import models


def public_user_uuids() -> Select:
    """Select public user uuids."""
    return sa.select(models.PublicUsers.user_uuid)


def ensure_registered_user_has_permissions(
        user: domain.User,
        stmt: Select,
) -> Select:
    """Ensure that registered user has permission to access this."""
    return stmt.select_from(
        models.Item.__table__.join(
            models.ComputedPermissions,  # type: ignore
            models.Item.uuid == models.ComputedPermissions.item_uuid,
            isouter=True,
        )
    ).where(
        sa.or_(
            models.Item.owner_uuid == str(user.uuid),
            models.ComputedPermissions.permissions.any(str(user.uuid)),
        )
    )


def ensure_anon_user_has_permissions(
        stmt: Select,
) -> Select:
    """Ensure that anon user has permission to access this."""
    return stmt.where(
        models.Item.owner_uuid.in_(public_user_uuids())
    )


def ensure_user_has_permissions(
        user: domain.User,
        stmt: Select,
) -> Select:
    """Ensure that any user has permission to access this."""
    if user.is_anon():
        return ensure_anon_user_has_permissions(stmt)
    return ensure_registered_user_has_permissions(user, stmt)
