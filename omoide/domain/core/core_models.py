"""Business-logic models.
"""
from dataclasses import dataclass

from omoide.infra import impl


@dataclass
class EXIF:
    """EXIF information embedded in media."""
    item_uuid: impl.UUID
    exif: dict[str, str | float | int | bool | None | list | dict]
