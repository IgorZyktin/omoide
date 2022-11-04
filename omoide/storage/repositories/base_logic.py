# -*- coding: utf-8 -*-
"""Core logic of the base repository.
"""
import abc
from typing import Any

from omoide.domain import interfaces


class BaseRepositoryLogic(interfaces.AbsRepository, abc.ABC):
    """Core logic of the base repository."""

    def __init__(self, db) -> None:
        """Initialize instance."""
        self.db = db

    def transaction(self) -> Any:
        """Start transaction."""
        return self.db.transaction()
