"""Common config options."""

from dataclasses import dataclass
from typing import Annotated

import nano_settings as ns


@dataclass
class Log(ns.BaseConfig):
    """Logging configuration."""

    path: str = ''
    level: str = 'DEBUG'
    rotation: str = '1 week'
    diagnose: Annotated[bool, ns.Boolean()] = True


@dataclass
class Db(ns.BaseConfig):
    """Database configuration."""

    url: ns.SecretStr
    echo: Annotated[bool, ns.Boolean()] = False


@dataclass
class Metrics(ns.BaseConfig):
    """Metrics configuration."""

    enabled: Annotated[bool, ns.Boolean()] = True
    address: str = '0.0.0.0'
    port: int = 9001
