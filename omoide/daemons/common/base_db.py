# -*- coding: utf-8 -*-
"""Generic database wrapper."""
import contextlib
from typing import Any
from typing import Optional

import sqlalchemy
import ujson
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide.daemons.common.meta_cfg import MetaConfig
from omoide.storage.database import models


class BaseDatabase:
    """Generic database wrapper."""

    def __init__(self, db_url: str) -> None:
        """Initialize instance."""
        self._db_url = db_url
        self._engine: Optional[Engine] = None
        self._session: Optional[Session] = None

    @property
    def engine(self) -> Engine:
        """Engine getter."""
        if self._engine is None:
            raise RuntimeError('You must use life_cycle context manager')
        return self._engine

    @engine.setter
    def engine(self, new_engine: Engine) -> None:
        """Engine setter."""
        self._engine = new_engine

    @property
    def session(self) -> Session:
        """Session getter."""
        if self._session is None:
            raise RuntimeError('You must use start_session context manager')
        return self._session

    @session.setter
    def session(self, new_session: Optional[Session]) -> None:
        """Session setter."""
        self._session = new_session

    @contextlib.contextmanager
    def life_cycle(self, echo: bool = False):
        """Ensure that connection is closed at the end."""
        self.engine = sqlalchemy.create_engine(
            self._db_url,
            echo=echo,
            pool_pre_ping=True,
        )

        try:
            yield
        finally:
            self.engine.dispose()

    @contextlib.contextmanager
    def start_session(self):
        """Wrapper around SA session."""
        with Session(self.engine) as session:
            self.session = session
            yield
        self.session = None

    def get_meta_config(self) -> MetaConfig:
        """Load meta config from the database."""
        values = self._get_meta_config_values()
        params = parse_meta_config_values(values)
        return MetaConfig(**params)

    def _get_meta_config_values(self) -> list[models.MetaConfigEntry]:
        """Load config values from DB."""
        return self.session.query(models.MetaConfigEntry).all()


def parse_meta_config_value(raw_value: str, target_type: str) -> Any:
    """Convert meta value to appropriate type."""
    target_type = target_type.lower()

    if target_type == 'str':
        result = str(raw_value)
    elif target_type == 'int':
        result = int(raw_value)
    elif target_type == 'float':
        result = float(raw_value)
    elif target_type == 'json':
        result = ujson.loads(raw_value)
    elif target_type == 'none':
        result = None
    else:
        raise RuntimeError(f'Unknown target type: {target_type!r}')

    return result


def parse_meta_config_values(
        values: list[models.MetaConfigEntry],
) -> dict[str, Any]:
    """Convert meta config values to appropriate types."""
    params: dict[str, Any] = {}

    for each in values:
        valid_value = parse_meta_config_value(each.value, each.type)
        params[each.key] = valid_value

    return params
