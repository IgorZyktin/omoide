# -*- coding: utf-8 -*-
"""Special class that works with filesystem.
"""
import os.path
from pathlib import Path

from omoide import utils
from omoide.infra import custom_logging


class Filesystem:
    """Special class that works with filesystem.
    """

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
            path: Path,
            filename: str,
            content: bytes,
    ) -> None:
        """Save file but not overwrite."""
        old_path = path / filename
        target_path = old_path

        while old_path.exists():
            new_name = self.make_new_filename(filename)
            new_path = path / new_name

            if new_path.exists():
                continue

            logger.debug('Renaming {} to {}', old_path, new_name)
            old_path.replace(new_path)
            break

        logger.debug('Saving {}', target_path)
        target_path.write_bytes(content)

    @staticmethod
    def make_new_filename(filename: str) -> str:
        """Generate new name to save existing file."""
        name, ext = os.path.splitext(filename)
        moment = utils.now().isoformat()
        return f'{name}___{moment}{ext}'
