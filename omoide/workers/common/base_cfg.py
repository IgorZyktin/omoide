"""Worker configuration."""
from pydantic import SecretStr
from pydantic_settings import BaseSettings


class BaseWorkerConfig(BaseSettings):
    """Worker configuration."""
    db_admin_url: SecretStr
    name: str = 'dev'
    short_delay: float = 1.0
    long_delay: float = 5.0
