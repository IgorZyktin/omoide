"""Raw models that come from user.
"""
import pydantic


class InEXIF(pydantic.BaseModel):
    """Input info for EXIF creation."""
    exif: dict[str, str | float | int | bool | None | list | dict]
