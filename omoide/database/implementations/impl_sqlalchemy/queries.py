"""Common database queries."""

import sqlalchemy as sa
from sqlalchemy.orm import aliased
from sqlalchemy.sql import Select

from omoide import const
from omoide import models
from omoide.database import db_models


def public_user_ids() -> Select:
    """Select public user ids."""
    return sa.select(db_models.User.id).where(db_models.User.is_public)


def item_is_public() -> sa.BinaryExpression:
    """Return condition that check that owner of the item is public."""
    return db_models.Item.owner_id.in_(public_user_ids())


def get_items_with_parent_names() -> Select:
    """Construct request that gathers names of item parents."""
    parents = aliased(db_models.Item)
    query = (
        sa.select(
            db_models.Item, sa.func.coalesce(parents.name, db_models.Item.name).label('parent_name')
        )
        .join(parents, parents.id == db_models.Item.parent_id, isouter=True)
        .where(db_models.Item.status != models.Status.DELETED)
    )
    return query


def ensure_registered_user_has_permissions(
    user: models.User,
    stmt: Select,
) -> Select:
    """Ensure that registered user has permission to access this."""
    return stmt.where(
        sa.or_(
            db_models.Item.owner_id == user.id,
            db_models.Item.permissions.any_() == user.id,
        )
    )


def ensure_anon_user_has_permissions(
    stmt: Select,
) -> Select:
    """Ensure that anon user has permission to access this."""
    return stmt.where(db_models.Item.owner_id.in_(public_user_ids()))


def ensure_user_has_permissions(
    user: models.User,
    stmt: Select,
) -> Select:
    """Ensure that any user has permission to access this."""
    if user.is_anon:
        return ensure_anon_user_has_permissions(stmt)
    return ensure_registered_user_has_permissions(user, stmt)


def apply_order(stmt: Select, plan: models.Plan) -> Select:
    """Limit query if user demands it."""
    if plan.order == const.ASC:
        stmt = stmt.order_by(db_models.Item.number)

        if plan.last_seen is not None and plan.last_seen > 0:
            stmt = stmt.where(db_models.Item.number > plan.last_seen)

    elif plan.order == const.DESC:
        stmt = stmt.order_by(sa.desc(db_models.Item.number))

        if plan.last_seen is not None and plan.last_seen > 0:
            stmt = stmt.where(db_models.Item.number < plan.last_seen)

    else:
        stmt = stmt.order_by(sa.func.random())

    return stmt


def finalize_query(query: Select, plan: models.Plan) -> Select:
    """Apply all final tweaks to the query."""
    return apply_order(query, plan).limit(plan.limit)
