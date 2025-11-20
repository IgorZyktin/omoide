"""Web level API models."""

from typing import Any
from typing import Self

from pydantic import BaseModel
from pydantic import model_validator
import python_utilz as pu

MAX_EXIF_SIZE = 1024 * 1024 * 5  # 5 MiB
MAX_EXIF_SIZE_HR = pu.human_readable_size(MAX_EXIF_SIZE)


class EXIFIn(BaseModel):
    """Input info for EXIF creation."""

    exif: dict[str, Any]

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'Make': 'SONY',
                    'Flash': 'Flash did not fire, auto mode',
                    'Model': 'DSC-S600',
                    'FNumber': 2.8,
                    'Contrast': 'Normal',
                    'DateTime': '2007:08:10 08:23:29',
                    'thumbnail': {
                        'ImageWidth': 512,
                        'ImageHeight': 384,
                    },
                }
            ]
        }
    }

    @model_validator(mode='after')
    def ensure_exif_is_not_too_big(self) -> Self:
        """Raise if given object is too big."""
        size = pu.get_size(self.exif)
        if size > MAX_EXIF_SIZE:
            hr_size = pu.human_readable_size(size)
            msg = (
                f'Given EXIF is too big (got {hr_size}), '
                f'allowed maximum is {MAX_EXIF_SIZE_HR}'
            )
            raise ValueError(msg)
        return self
