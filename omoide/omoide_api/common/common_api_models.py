"""Web level API models."""

from typing import Any
from typing import Self
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator

from omoide import limits
from omoide import models


class Permission(BaseModel):
    """Human-readable representation of a permission entry."""

    uuid: UUID
    name: str


class ItemInput(BaseModel):
    """Input info for item creation."""

    uuid: UUID | None = None
    parent_uuid: UUID | None = None
    name: str = Field('', max_length=limits.MAX_ITEM_FIELD_LENGTH)
    number: int | None = None
    is_collection: bool = False
    tags: list[str] = Field([], max_length=limits.MAX_TAGS)
    permissions: list[Permission] = Field([], max_length=limits.MAX_PERMISSIONS)

    @model_validator(mode='after')
    def check_tags(self) -> Self:
        """Raise if tag is too big."""
        for tag in self.tags:
            if len(tag) > limits.MAX_ITEM_FIELD_LENGTH:
                msg = (
                    f'Tag is too long ({len(tag)} symbols), '
                    f'max allowed length is {limits.MAX_ITEM_FIELD_LENGTH} symbols'
                )
                raise ValueError(msg)
        return self

    @model_validator(mode='after')
    def ensure_collection_has_name(self) -> Self:
        """Raise if got nameless collection."""
        if self.is_collection and not self.name:
            msg = 'Collection must have a name'
            raise ValueError(msg)
        return self


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
    tags: list[str] = []
    permissions: list[Permission] = []
    extras: dict[str, Any] = {}


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
    },
}


class OneItemOutput(BaseModel):
    """Response with one item."""

    item: ItemOutput

    model_config = {
        'json_schema_extra': {
            'examples': [{'item': DEFAULT_ITEM_EXAMPLE}],
        }
    }


class ManyItemsOutput(BaseModel):
    """Response with many items."""

    duration: float
    items: list[ItemOutput]

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'duration': 0.025,
                    'items': [DEFAULT_ITEM_EXAMPLE],
                }
            ],
        }
    }


class ItemDeleteOutput(BaseModel):
    """Output info after item deletion."""

    result: str
    item_uuid: str
    switch_to: ItemOutput | None


def convert_item(item: models.Item, users: dict[int, models.User | None]) -> ItemOutput:
    """Convert domain-level item into API format."""
    return convert_items([item], users)[0]


def convert_items(
    items: list[models.Item],
    users: dict[int, models.User | None],
) -> list[ItemOutput]:
    """Convert domain-level items into API format."""
    return [
        ItemOutput(
            **item.model_dump(exclude={'permissions'}),
            permissions=[
                Permission(
                    uuid=user.uuid,
                    name=user.name,
                )
                for user in users.get(item.id, [])
            ],
        )
        for item in items
    ]
