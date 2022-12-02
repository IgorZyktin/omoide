# -*- coding: utf-8 -*-
"""Generic database wrapper."""
import contextlib
from typing import Optional

import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


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
