"""Web level API models."""
from uuid import UUID

import pydantic
from pydantic import BaseModel


class RebuildKnownTagsInput(BaseModel):
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


class RebuildComputedTagsInput(BaseModel):
    """Info about target user for tag rebuilding."""
    user_uuid: UUID
    including_children: bool = True

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'user_uuid': '3efa5072-a225-4b43-9a13-3a7833ca74b7',
                    'including_children': True,
                },
            ]
        }
    }


class CopyContentInput(BaseModel):
    """Info about affected items."""
    source_item_uuid: UUID
    target_item_uuid: UUID

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'source_item_uuid': '281585ec-aed0-4518-b9df-1d2d446d249b',
                    'target_item_uuid': 'acc45593-fe9e-46dc-bd99-72d373dcac3f',
                },
            ]
        }
    }

    @pydantic.model_validator(mode="after")
    def check_not_the_same(self) -> 'CopyContentInput':
        """Check items are not the same."""
        if self.source_item_uuid == self.target_item_uuid:
            msg = 'You cannot copy item content to itself'
            raise ValueError(msg)

        return self
