# -*- coding: utf-8 -*-
"""Special class that works with filesystem.
"""
import os.path
from pathlib import Path
from typing import Any
from typing import NoReturn
from typing import Optional

import ujson

from omoide import utils
from omoide.infra import custom_logging
from omoide.storage.database import models


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

    @staticmethod
    def raise_if_not_exist(
            *args: str,
    ) -> Optional[NoReturn]:
        """Create folder if needed."""
        path = Path().joinpath(*args)

        if not path.exists():
            raise FileNotFoundError(f'Path {path} does not exist!')

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

    def execute_operation(
            self,
            folder: str,
            operation: models.FilesystemOperation,
            prefix_size: int,
    ) -> bytes:
        """Execute generic operation."""
        extras = ujson.loads(str(operation.extras))

        if operation.operation == 'copy-thumbnail':
            result = self.execute_copy_thumbnail(
                folder=folder,
                operation=operation,
                extras=extras,
                prefix_size=prefix_size,
            )
        else:
            raise RuntimeError(f'Unknown operation: {operation.operation!r}')

        return result

    @staticmethod
    def execute_copy_thumbnail(
            folder: str,
            operation: models.FilesystemOperation,
            extras: dict[str, Any],
            prefix_size: int,
    ) -> bytes:
        """Copy thumbnail from one item to another."""
        ext = extras['ext']
        bucket = utils.get_bucket(operation.source_uuid, prefix_size)

        filename = Path().joinpath(
            folder,
            'thumbnails',
            extras['owner_uuid'],
            bucket,
            f'{operation.source_uuid}.{ext}',
        )

        content = filename.read_bytes()
        return content
