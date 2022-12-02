# -*- coding: utf-8 -*-
"""Special class that works with filesystem.
"""
import os.path
from pathlib import Path

from omoide import utils
from omoide.infra import custom_logging


class Filesystem:
    """Special class that works with filesystem."""

    @staticmethod
    def ensure_folder_exists(
            logger: custom_logging.Logger,
            *args: str,
    ) -> Path:
        """Create folder if needed."""
        path = Path().joinpath(*args)

        if not path.exists():
            logger.debug('Creating path {}', path)

        path.mkdir(parents=True, exist_ok=True)
        return path

    def safely_save(
            self,
            logger: custom_logging.Logger,
            path: str | Path,
            filename: str,
            content: bytes,
    ) -> Path:
        """Save file but not overwrite."""
        old_path = Path(path) / filename
        target_path = old_path

        while old_path.exists():
            new_filename = self.make_new_filename(filename)
            new_path = path / new_filename

            if new_path.exists():
                logger.debug('New name is already taken: {}', new_path)
                continue

            logger.debug('Renaming {} to {}', old_path, new_filename)
            old_path.replace(new_path)
            break

        logger.debug('Saving {}', target_path)
        target_path.write_bytes(content)
        return target_path

    @staticmethod
    def make_new_filename(filename: str, separator: str = '___') -> str:
        """Generate new name using old name."""
        name, ext = os.path.splitext(filename)
        left_segment, *_ = name.split(separator)
        moment = utils.now().isoformat()
        return f'{left_segment}{separator}{moment}{ext}'

    @staticmethod
    def load_from_filesystem(*args: str | Path) -> bytes:
        """Load binary data from filesystem."""
        filename = Path().joinpath(*args)
        content = filename.read_bytes()
        return content
