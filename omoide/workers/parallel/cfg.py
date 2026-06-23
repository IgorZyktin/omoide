"""Worker configuration."""

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import nano_settings as ns

from omoide.workers.common import cfg


@dataclass
class ParallelWorkerConfig(ns.BaseConfig):
    """Worker configuration."""

    db: cfg.Db
    log: cfg.Log
    metrics: cfg.Metrics

    name: str = 'parallel-dev'
    delay: float = 1.0
    input_batch: int = 10
    supported_operations: Annotated[
        frozenset[str], frozenset, ns.Separated()
    ] = frozenset()
    data_folder: Path = Path('.')
    temp_folder: Path = Path('.')
    # zero means select automatically, but not more than `max_workers`
    workers: int = 0
    max_workers: int = 5
    prefix_size: int = 2
    shutdown_deadline: float = 300.0
