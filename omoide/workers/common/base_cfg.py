"""Worker configuration."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings

from omoide import const


class BaseWorkerConfig(BaseSettings):
    """Worker configuration."""

    db_admin_url: SecretStr
    name: str = 'dev'
    short_delay: float = 0.0
    long_delay: float = 5.0
    input_batch: int = 100
    output_batch: int = 100
    supported_operations: list[str] = [const.DUMMY_OPERATION]
