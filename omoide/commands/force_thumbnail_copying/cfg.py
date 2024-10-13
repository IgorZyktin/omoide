"""Command configuration."""

from pydantic import BaseModel
from pydantic import SecretStr


class Config(BaseModel):
    """Command configuration."""

    db_url: SecretStr
    only_users: list[str]
