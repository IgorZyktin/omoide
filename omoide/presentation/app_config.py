"""Application settings."""

from typing import Any

import pydantic
import pydantic_settings


class MiddlewareDescription(pydantic.BaseModel):
    """Entry that describes middlewares."""

    name: str
    config: dict[str, Any]


class Config(pydantic_settings.BaseSettings):
    """Application settings."""

    db_url_app: pydantic.SecretStr
    env: str = 'dev'
    host: str = '0.0.0.0'
    prefix_size: int = 2
    penalty_wrong_password: float = 2.5
    middlewares: list[MiddlewareDescription] = []

    model_config = pydantic_settings.SettingsConfigDict(
        env_prefix='omoide_',
    )
