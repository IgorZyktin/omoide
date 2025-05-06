"""Worker configuration."""

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import nano_settings as ns


@dataclass
class SerialWorkerConfig(ns.BaseConfig):
    """Worker configuration."""

    db_url: ns.SecretStr

    data_folder: Path
    prefix_size: int

    log_path: str = ''
    log_level: str = 'DEBUG'
    log_rotation: str = '1 week'
    log_diagnose: Annotated[bool, ns.Boolean()] = True

    name: str = 'serial-dev'
    short_delay: float = 0.0
    long_delay: float = 5.0
    input_batch: int = 10
    output_batch: int = 100
    supported_operations: Annotated[frozenset[str], frozenset, ns.Separated()] = frozenset()
