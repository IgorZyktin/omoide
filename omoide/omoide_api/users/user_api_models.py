"""Web level API models."""

from typing import Any

from pydantic import BaseModel
from pydantic import Field

MIN_LENGTH_FOR_USER_LOGIN = 2
MIN_LENGTH_FOR_USER_NAME = MIN_LENGTH_FOR_USER_LOGIN
MIN_LENGTH_FOR_USER_PASSWORD = 8
MAX_LENGTH_FOR_USER_FILED = 1024


class UserInput(BaseModel):
    """Simple user format."""

    name: str = Field(
        ...,
        min_length=MIN_LENGTH_FOR_USER_NAME,
        max_length=MAX_LENGTH_FOR_USER_FILED,
    )
    login: str = Field(
        ...,
        min_length=MIN_LENGTH_FOR_USER_LOGIN,
        max_length=MAX_LENGTH_FOR_USER_FILED,
    )
    password: str = Field(
        ...,
        min_length=MIN_LENGTH_FOR_USER_PASSWORD,
        max_length=MAX_LENGTH_FOR_USER_FILED,
    )

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'name': 'John Smith',
                    'login': 'john',
                    'password': 'qwerty-for-real',
                },
                {
                    'name': 'Samantha Smith',
                    'login': 'sammy',
                    'password': 'qwerty11',
                },
            ]
        }
    }


class UserValueInput(BaseModel):
    """New name/login/password."""

    value: str = Field(..., max_length=MAX_LENGTH_FOR_USER_FILED)


class UserOutput(BaseModel):
    """Simple user format."""

    uuid: str
    name: str
    extras: dict[str, Any]

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'uuid': '7925f364-2a51-48f0-b15c-7be4d3b60ef4',
                    'name': 'John Smith',
                    'extras': {
                        'root_item_uuid': '820bdef1-f4a9-41dc-b717-b4204dc2fc73',
                    },
                },
            ]
        }
    }


class UserCollectionOutput(BaseModel):
    """Collection of users."""

    users: list[UserOutput]


class UserResourceUsageOutput(BaseModel):
    """Total resource usage for specific user."""

    user_uuid: str
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
                    'user_uuid': '66292021-e68b-4cbb-a511-9f23a9256b5b',
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
