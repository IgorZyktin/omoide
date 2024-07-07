"""Common database queries."""
import sqlalchemy as sa
from sqlalchemy.sql import Select

from omoide import models
from omoide.storage.database import db_models


def public_user_uuids() -> Select:
    """Select public user uuids."""
    return sa.select(db_models.PublicUsers.user_uuid)


def ensure_registered_user_has_permissions(
        user: models.User,
        stmt: Select,
) -> Select:
    """Ensure that registered user has permission to access this."""
    return stmt.where(
        sa.or_(
            db_models.Item.owner_uuid == str(user.uuid),
            db_models.Item.permissions.any(str(user.uuid)),
        )
    )


def ensure_anon_user_has_permissions(
        stmt: Select,
) -> Select:
    """Ensure that anon user has permission to access this."""
    return stmt.where(
        db_models.Item.owner_uuid.in_(public_user_uuids())  # noqa
    )


def ensure_user_has_permissions(
        user: models.User,
        stmt: Select,
) -> Select:
    """Ensure that any user has permission to access this."""
    if user.is_anon:
        return ensure_anon_user_has_permissions(stmt)
    return ensure_registered_user_has_permissions(user, stmt)
