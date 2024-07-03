"""Web level API models."""
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


class UserCollectionOutput(BaseModel):
    """Collection of users."""
    users: list[UserOutput]


class UserStatsOutput(BaseModel):
    """Statistics for user."""
    total_items: int
    total_collections: int
    content_bytes: int
    content_hr: str
    preview_bytes: int
    preview_hr: str
    thumbnail_bytes: int
    thumbnail_hr: str

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'total_items': 2735,
                    'total_collections': 22,
                    'content_bytes': 1177374884,
                    'content_hr': '1.1 GiB',
                    'preview_bytes': 256635453,
                    'preview_hr': '244.7 MiB',
                    'thumbnail_bytes': 62661090,
                    'thumbnail_hr': '59.8 MiB',
                },
            ]
        }
    }
