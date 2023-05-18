# -*- coding: utf-8 -*-
"""Special wrappers for common tools, allows changing of implementation.
"""
from typing import TypeAlias
from uuid import UUID as _UUID

import ujson

UUID = _UUID

JSON: TypeAlias = dict[str, str | float | int | bool | None | list | dict]

json = ujson
