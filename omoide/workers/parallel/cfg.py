"""Worker configuration."""

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import nano_settings as ns
import ujson


@dataclass
class ParallelWorkerConfig(ns.BaseConfig):
    """Worker configuration."""

    db_url: ns.SecretStr

    log_path: str = ''
    log_level: str = 'DEBUG'
    log_rotation: str = '1 week'
    log_diagnose: Annotated[bool, ns.looks_like_boolean] = True

    name: str = 'parallel-dev'
    fork_type: str = 'process'
    short_delay: float = 0.0
    long_delay: float = 5.0
    input_batch: int = 100
    supported_operations: Annotated[frozenset[str], frozenset, ujson.loads] = frozenset()
    data_folder: Path = Path('.')
    workers: int = 0
    max_workers: int = 5
