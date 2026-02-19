"""Worker configuration."""

from dataclasses import dataclass

import nano_settings as ns

from omoide.workers.common import cfg


@dataclass
class WorkerConverterConfig(ns.BaseConfig):
    """Worker configuration."""

    db: cfg.Db
    log: cfg.Log

    name: str = 'converter-dev'
    short_delay: float = 0.0
    long_delay: float = 1.0
    input_batch: int = 10
