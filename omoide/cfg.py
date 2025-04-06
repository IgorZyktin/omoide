"""Application settings."""

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import python_utilz as pu
import ujson


@dataclass
class Config(pu.BaseConfig):
    """Application settings."""

    db_url: pu.SecretStr
    data_folder: Path
    static_folder: Path = Path('omoide/presentation/static')
    env: str = 'dev'
    host: str = '0.0.0.0'
    port: int = 8080
    prefix_size: int = 2

    penalty_wrong_password: float = 2.5  # seconds
    allowed_origins: Annotated[tuple[str, ...], tuple, ujson.loads] = (
        'http://localhost',
        'http://localhost:8080',
    )
