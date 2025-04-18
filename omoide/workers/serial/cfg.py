"""Worker configuration."""

from dataclasses import dataclass
from typing import Annotated

import nano_settings as ns
import ujson


@dataclass
class SerialWorkerConfig(ns.BaseConfig):
    """Worker configuration."""

    db_url: ns.SecretStr
    log_path: str = ''
    name: str = 'serial-dev'
    short_delay: float = 0.0
    long_delay: float = 5.0
    input_batch: int = 100
    output_batch: int = 100
    supported_operations: Annotated[frozenset[str], frozenset, ujson.loads] = frozenset()
