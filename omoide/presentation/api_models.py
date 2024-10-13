"""Input and output models for the API."""

from uuid import UUID

import pydantic


class PatchOperation(pydantic.BaseModel):
    """Single operation in PATCH request."""

    op: str
    path: str
    value: str | bool | None = None


class NewTagsIn(pydantic.BaseModel):
    """Input info for new tags."""

    tags: list[str]
    # TODO - add validation


class NewPermissionsIn(pydantic.BaseModel):
    """Input info for new permissions."""

    apply_to_parents: bool
    apply_to_children: bool
    override: bool
    permissions_before: list[UUID]
    permissions_after: list[UUID]
