# -*- coding: utf-8 -*-
"""Filesystem related tools."""
import os
import sys
from pathlib import Path
from typing import Optional


def extract_paths(folders: Optional[str]) -> list[Path]:
    """Parse input, check existence of folders, return list of paths."""
    if not folders:
        print('No folders specified')
        sys.exit(1)

    paths = [Path(x.strip()) for x in folders.split(';') if x]

    for path in paths:
        if not path.exists():
            print(f'Path does not exist: {path!r}')
            sys.exit(1)

    return paths


def drop_if_exists(filename: str) -> None:
    """Try deleting file before saving."""
    try:
        os.remove(filename)
    except FileNotFoundError:
        pass


def create_folders_for_filename(path: Path, *segments: str) -> str:
    """Combine filename, create folders if need to."""
    for i, segment in enumerate(segments, start=1):
        path /= segment

        if not path.exists() and i != len(segments):
            os.mkdir(path)

    return str(path.absolute())
