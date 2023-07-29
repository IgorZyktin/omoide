"""Business-logic models.
"""
from dataclasses import dataclass
from uuid import UUID


@dataclass(eq=True)
class EXIF:
    """EXIF information embedded in media."""
    item_uuid: UUID
    exif: dict[str, str | float | int | bool | None | list | dict]
