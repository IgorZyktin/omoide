# -*- coding: utf-8 -*-
"""Application models.
"""
from pydantic import BaseModel

from omoide.infra import impl


class AppModel(BaseModel):
    """Base class for all application models."""


class RawEXIF(AppModel):
    """Raw EXIF."""
    exif: impl.JSON
