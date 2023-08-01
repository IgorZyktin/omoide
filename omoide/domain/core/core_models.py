"""Business-logic models.
"""
from dataclasses import dataclass
from uuid import UUID

from omoide.domain import auth

# FIXME - temporary import
User = auth.User


@dataclass(eq=True)
class EXIF:
    """EXIF information embedded in media."""
    item_uuid: UUID
    exif: dict[str, str | float | int | bool | None | list | dict]
