"""Web level API models.
"""
from typing import Any

from pydantic import BaseModel


class UserOutput(BaseModel):
    """Simple user format."""
    uuid: str
    name: str
    extra: dict[str, Any]

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'uuid': '7925f364-2a51-48f0-b15c-7be4d3b60ef4',
                    'name': 'John Smith',
                    'extra': {
                        'root_item': '820bdef1-f4a9-41dc-b717-b4204dc2fc73',
                    },
                },
                {
                    'uuid': 'e45801c1-5977-4669-9f9f-01a20b93421d',
                    'name': 'Ladybug',
                    'extra': {
                        'root_item': None,
                    },
                }
            ]
        }
    }
