"""Worker configuration."""

from dataclasses import dataclass
from pathlib import Path

import nano_settings as ns

from omoide.workers.common import cfg


@dataclass
class WorkerConverterConfig(ns.BaseConfig):
    """Worker configuration."""

    db: cfg.Db
    log: cfg.Log
    metrics: cfg.Metrics

    temp_folder: Path

    name: str = 'converter-dev'
    short_delay: float = 0.0
    long_delay: float = 1.0
    exc_delay: float = 10.0
    input_batch: int = 10
