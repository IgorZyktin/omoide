"""Worker configuration."""

from pydantic_settings import SettingsConfigDict

from omoide.workers.common.base_cfg import BaseWorkerConfig


class Config(BaseWorkerConfig):
    """Worker configuration."""

    model_config = SettingsConfigDict(
        env_prefix='omoide_worker_serial__',
    )
