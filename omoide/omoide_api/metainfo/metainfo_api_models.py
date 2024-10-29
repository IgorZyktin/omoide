"""Web level API models."""

from pydantic import BaseModel


class MetainfoOutput(BaseModel):
    """Metainfo for item."""

    created_at: str
    updated_at: str
    deleted_at: str | None = None
    user_time: str | None = None
    content_type: str | None = None

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
                    'user_time': '2022-02-16 19:51:14.321331+00:00',
                    'content_type': 'image/jpeg',
                    'content_width': 2104,
                    'content_height': 1480,
                    'preview_width': 1456,
                    'preview_height': 1024,
                    'thumbnail_width': 548,
                    'thumbnail_height': 384,
                }
            ]
        }
    }
