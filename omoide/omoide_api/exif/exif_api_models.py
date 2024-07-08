"""Web level API models."""
from typing import Any

from pydantic import BaseModel


class EXIFModel(BaseModel):
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
                }
            ]
        }
    }
