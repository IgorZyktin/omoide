# -*- coding: utf-8 -*-
"""User defined manipulations.
"""
from PIL.Image import Image

from omoide.storage.database.models import Item


def apply_features(item: Item, image: Image) -> None:
    """Apply user defined manipulations."""
    # TODO
