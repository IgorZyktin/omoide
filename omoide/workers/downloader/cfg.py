"""Worker configuration."""

from dataclasses import dataclass

import nano_settings as ns

from omoide.workers.common import cfg


@dataclass
class WorkerDownloaderConfig(ns.BaseConfig):
    """Worker configuration."""

    db: cfg.Db
    log: cfg.Log
    metrics: cfg.Metrics

    name: str = 'downloader-dev'
    short_delay: float = 0.0
    long_delay: float = 1.0
    exc_delay: float = 10.0
    input_batch: int = 10
    workers: int = 0
    max_workers: int = 6
