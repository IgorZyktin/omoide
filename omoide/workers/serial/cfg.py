"""Worker configuration."""

from pydantic_settings import SettingsConfigDict

from omoide.workers.common.base_cfg import BaseWorkerConfig


class Config(BaseWorkerConfig):
    """Worker configuration."""

    model_config = SettingsConfigDict(
        env_prefix='omoide_worker_serial__',
    )


CONF: Config | None = None


def get_config() -> Config:
    """Get instance of config."""
    global CONF

    if CONF is None:
        CONF = Config()

    return CONF
