# -*- coding: utf-8 -*-
"""Filesystem related tools."""
import os
from pathlib import Path

__all__ = [
    'drop_if_exists',
    'create_folders_for_filename',
]


def drop_if_exists(filename: str) -> None:
    """Try deleting file before saving."""
    try:
        os.remove(filename)
    except FileNotFoundError:
        pass


def create_folders_for_filename(path: Path, *segments: str) -> str:
    """Combine filename, create folders if they do not exist."""
    for i, segment in enumerate(segments, start=1):
        path /= segment

        if not path.exists() and i != len(segments):
            os.mkdir(path)

    return str(path.absolute())
