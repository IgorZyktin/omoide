"""Web level API models."""
from datetime import datetime

from pydantic import BaseModel

_BASE_EXAMPLE = {
    'user_time': None,
    'content_type': 'image/jpeg',
    'author': None,
    'author_url': None,
    'saved_from_url': None,
    'description': None,
    'extras': {
        'original_file_name': 'IMG_6607.jpg'
    },
    'content_size': 1159935,
    'preview_size': 167872,
    'thumbnail_size': 39411,
    'content_width': 2104,
    'content_height': 1480,
    'preview_width': 1456,
    'preview_height': 1024,
    'thumbnail_width': 548,
    'thumbnail_height': 384,
}


class MetainfoInput(BaseModel):
    """Metainfo for item."""
    user_time: datetime | None = None

    content_type: str | None = None

    author: str | None = None
    author_url: str | None = None
    saved_from_url: str | None = None
    description: str | None = None

    extras: dict

    content_size: int | None = None
    preview_size: int | None = None
    thumbnail_size: int | None = None

    content_width: int | None = None
    content_height: int | None = None
    preview_width: int | None = None
    preview_height: int | None = None
    thumbnail_width: int | None = None
    thumbnail_height: int | None = None

    model_config = {
        'json_schema_extra': {
            'examples': [_BASE_EXAMPLE]
        }
    }


class MetainfoOutput(BaseModel):
    """Metainfo for item."""
    created_at: str
    updated_at: str
    deleted_at: str | None = None
    user_time: str | None = None

    content_type: str | None = None

    author: str | None = None
    author_url: str | None = None
    saved_from_url: str | None = None
    description: str | None = None

    extras: dict

    content_size: int | None = None
    preview_size: int | None = None
    thumbnail_size: int | None = None

    content_width: int | None = None
    content_height: int | None = None
    preview_width: int | None = None
    preview_height: int | None = None
    thumbnail_width: int | None = None
    thumbnail_height: int | None = None

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'created_at': '2022-02-16 19:51:14.321331+00:00',
                    'updated_at': '2022-02-16 19:51:14.321331+00:00',
                    'deleted_at': None,
                    **_BASE_EXAMPLE,
                }
            ]
        }
    }
