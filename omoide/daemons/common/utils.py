# -*- coding: utf-8 -*-
"""Helper functions for daemons.
"""
from pydantic import BaseSettings


def apply_cli_kwargs_to_config(config: BaseSettings, **kwargs) -> None:
    """Apply CLI settings to the config instance."""
    for key, value in kwargs.items():
        setattr(config, key, value)
