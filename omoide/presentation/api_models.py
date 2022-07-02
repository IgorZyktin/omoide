# -*- coding: utf-8 -*-
"""Input and output models for the API.
"""
from uuid import UUID

from pydantic import BaseModel


class OnlyUUID(BaseModel):
    """Simple model, that describes only UUID of the object."""
    uuid: UUID
