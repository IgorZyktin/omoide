# -*- coding: utf-8 -*-
"""Application models for user input.
"""
from pydantic import BaseModel

from omoide.infra import impl


class RawModel(BaseModel):
    """Base class for all application models."""


class RawEXIF(RawModel):
    """Raw EXIF."""
    exif: impl.JSON
