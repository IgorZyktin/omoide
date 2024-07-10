"""Web level API models."""
from typing import Any

from pydantic import BaseModel
from pydantic import model_validator


class UserInput(BaseModel):
    """Simple user format."""
    name: str
    login: str
    password: str

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'name': 'John Smith',
                    'login': 'john',
                    'password': 'qwerty',
                }
            ]
        }
    }


class UserUpdateInput(BaseModel):
    """Simple user format for user update."""
    name: str = ''
    login: str = ''
    password: str = ''

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'name': 'John Dow',
                },
                {
                    'password': '12345',
                }
            ]
        }
    }

    @model_validator(mode='after')
    def ensure_at_least_one_given(self) -> 'UserUpdateInput':  # TODO - Self
        """Raise if nothing is actually sent."""
        if not any(
            (
                self.name,
                self.login,
                self.password,
            )
        ):
            msg = 'You have to specify new name, new login, or new password'
            raise ValueError(msg)
        return self


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
                        'root_item': '820bdef1-f4a9-41dc-b717-b4204dc2fc73',
                    },
                },
                {
                    'uuid': 'e45801c1-5977-4669-9f9f-01a20b93421d',
                    'name': 'Ladybug',
                    'extras': {
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
    content_size: int
    content_size_hr: str
    preview_size: int
    preview_size_hr: str
    thumbnail_size: int
    thumbnail_size_hr: str

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'total_items': 2735,
                    'total_collections': 22,
                    'content_size': 1177374884,
                    'content_size_hr': '1.1 GiB',
                    'preview_size': 256635453,
                    'preview_size_hr': '244.7 MiB',
                    'thumbnail_size': 62661090,
                    'thumbnail_size_hr': '59.8 MiB',
                },
            ]
        }
    }
