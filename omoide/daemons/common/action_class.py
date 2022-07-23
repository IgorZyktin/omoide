# -*- coding: utf-8 -*-
"""Helper type that stores daemon actions.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from omoide import utils


class Action(BaseModel):
    """Helper type that stores daemon actions."""
    started_at: datetime = Field(default_factory=utils.now)
    ended_at: Optional[datetime] = None
    status: str

    def is_done(self) -> bool:
        """Return true if action is done."""
        return self.status == 'done'

    def is_failed(self) -> bool:
        """Return true if action is failed."""
        return self.status == 'fail'

    def fail(self) -> None:
        """Mark as failed."""
        self.status = 'fail'
        self.ended_at = utils.now()

    def done(self) -> None:
        """Mark as done."""
        self.status = 'done'
        self.ended_at = utils.now()
