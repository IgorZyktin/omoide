"""Worker configuration."""

from dataclasses import dataclass
from pathlib import Path

import python_utilz as pu


@dataclass
class ParallelWorkerConfig(pu.BaseConfig):
    """Worker configuration."""

    db_url: pu.SecretStr
    name: str = 'dev'
    short_delay: float = 0.0
    long_delay: float = 5.0
    input_batch: int = 100
    output_batch: int = 100
    supported_operations: frozenset[str] = frozenset()
    data_folder: Path = Path('.')
    workers: int = -1
    max_workers: int = 5
