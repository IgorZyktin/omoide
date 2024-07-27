"""Web level API models."""
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ItemOutput(BaseModel):
    """Model of a standard item."""
    uuid: UUID
    parent_uuid: UUID | None
    owner_uuid: UUID
    number: int
    name: str
    is_collection: bool
    content_ext: str | None
    preview_ext: str | None
    thumbnail_ext: str | None
    tags: list[str]
    permissions: list[UUID]
    extras: dict[str, Any]


DEFAULT_ITEM_EXAMPLE = {
    'uuid': '27c004fe-af9e-43af-9e1c-bf36c8ea57f2',
    'parent_uuid': '30f37bec-4e1b-430d-bbfb-80b3f41f2b44',
    'owner_uuid': 'fec6e0ac-9142-4ccd-bbae-af0fc9037b1a',
    'number': 129324,
    'name': '',
    'is_collection': False,
    'content_ext': 'jpg',
    'preview_ext': 'jpg',
    'thumbnail_ext': 'jpg',
    'tags': ['cats'],
    'permissions': ['2e81dc5a-fdc9-45ee-bd78-f276328a14bf'],
    'extras': {
        'parent_name': 'Cool cats',
    }
}
