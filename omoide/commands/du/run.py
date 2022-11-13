# -*- coding: utf-8 -*-
"""Disk Usage command.
"""
from sqlalchemy.engine import Engine

from omoide.commands.du.cfg import Config


def main(
        engine: Engine,
        config: Config,
):
    """Show disk usage for every user."""
    print(1)
