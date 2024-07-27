"""Web level API models."""
from uuid import UUID

from pydantic import BaseModel


class RebuildTagsInput(BaseModel):
    """Info about target user for tag rebuilding."""
    user_uuid: UUID | None

    model_config = {
        'json_schema_extra': {
            'examples': [
                {'user_uuid': '2613f5c6-2508-474b-b4cf-feab4987211e'},
                {'user_uuid': None},
            ]
        }
    }
