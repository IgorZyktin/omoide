"""Worker configuration."""

from pathlib import Path

from pydantic_settings import SettingsConfigDict

from omoide.workers.common.base_cfg import BaseWorkerConfig


class Config(BaseWorkerConfig):
    """Worker configuration."""

    folder: Path
    workers: int | None = None
    max_workers: int = 5

    model_config = SettingsConfigDict(
        env_prefix='omoide_worker_parallel__',
    )
