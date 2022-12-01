# -*- coding: utf-8 -*-
"""Database tools for worker.
"""
from omoide.daemons.common.base_db import BaseDatabase


class Database(BaseDatabase):
    """Wrapper on SQL commands for worker."""
