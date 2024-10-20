"""Worker configuration."""

from pydantic import Field
from pydantic import SecretStr
from pydantic_settings import BaseSettings


class BaseWorkerConfig(BaseSettings):
    """Worker configuration."""

    db_admin_url: SecretStr
    name: str = 'dev'
    short_delay: float = 0.0
    long_delay: float = 5.0
    input_batch: int = 100
    output_batch: int = 100
    supported_operations: list[str] = Field(default_factory=list)
