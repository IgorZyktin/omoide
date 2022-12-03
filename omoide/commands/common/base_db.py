# -*- coding: utf-8 -*-
"""Generic database wrapper."""
import contextlib
from typing import Generator
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide import utils
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

    @contextlib.contextmanager
    def life_cycle(self, echo: bool = False) -> Generator[Engine, None, None]:
        """Ensure that connection is closed at the end."""
        self.engine = sa.create_engine(
            self._db_url,
            echo=echo,
            pool_pre_ping=True,
        )

        try:
            yield self.engine
        finally:
            self.engine.dispose()

    @contextlib.contextmanager
    def start_session(self) -> Generator[Session, None, None]:
        """Wrapper around SA session."""
        with Session(self.engine) as session:
            yield session

    def save_statistic(self, key: str, value: int) -> None:
        """Save arbitrary statistic."""
        stmt = sa.insert(
            models.Statistic
        ).values(
            moment=utils.now(),
            key=key,
            value=value,
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)
