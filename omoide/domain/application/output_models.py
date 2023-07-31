"""Models that go to user.
"""
from uuid import UUID

import pydantic


class OutEXIF(pydantic.BaseModel):
    """Input info for EXIF creation."""
    item_uuid: UUID
    exif: dict[str, str | float | int | bool | None | list | dict]
