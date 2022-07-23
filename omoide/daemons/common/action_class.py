# -*- coding: utf-8 -*-
"""Helper type that stores daemon actions.
"""
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field

from omoide import utils


class Action(BaseModel):
    """Helper type that stores daemon actions."""
    started_at: datetime = Field(default_factory=utils.now)
    ended_at: Optional[datetime]
    status: str = Literal['init', 'work', 'done', 'failed']

    def is_done(self) -> bool:
        """Return true if action is done."""
        return self.status == 'done'

    def is_failed(self) -> bool:
        """Return true if action is failed."""
        return self.status == 'failed'
