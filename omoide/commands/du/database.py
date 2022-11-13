# -*- coding: utf-8 -*-
"""Database helpers.
"""
from uuid import UUID

import sqlalchemy
from sqlalchemy.engine import Engine

from omoide import domain
from omoide.storage.database import models

_USERS_CACHE: dict[UUID, domain.User] = {}


def get_user(
        engine: Engine,
        uuid: UUID,
) -> domain.User | None:
    """Load user from the database."""
    user = _USERS_CACHE.get(uuid)

    if user is not None:
        return user

    stmt = sqlalchemy.select(
        models.User
    ).where(
        models.User.uuid == str(uuid)
    )

    with engine.begin() as conn:
        raw_user = conn.execute(stmt).first()

    if raw_user is not None:
        _uuid, _login, _password, _name, _root_item = raw_user
        user = domain.User(
            uuid=_uuid,
            login=_login,
            password=_password,
            name=_name,
            root_item=_root_item,
        )
        _USERS_CACHE[uuid] = user

    return user or None
