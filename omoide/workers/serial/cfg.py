"""Worker configuration."""

from dataclasses import dataclass
from typing import Annotated

import python_utilz as pu
import ujson


@dataclass
class SerialWorkerConfig(pu.BaseConfig):
    """Worker configuration."""

    db_url: pu.SecretStr
    name: str = 'dev'
    short_delay: float = 0.0
    long_delay: float = 5.0
    input_batch: int = 100
    output_batch: int = 100
    supported_operations: Annotated[frozenset[str], ujson.loads, frozenset] = frozenset()
