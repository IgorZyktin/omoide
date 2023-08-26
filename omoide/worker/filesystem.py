"""Special class that works with filesystem.
"""
import os.path
from pathlib import Path

from omoide import utils
from omoide.infra import custom_logging
from omoide.worker.worker_config import Config

LOG = custom_logging.get_logger(__name__)


class Filesystem:
    """Special class that works with filesystem."""

    def __init__(self, config: Config) -> None:
        """Initialize instance."""
        self._config = config

    @staticmethod
    def ensure_folder_exists(*args: str) -> Path:
        """Create folder if needed."""
        path = Path().joinpath(*args)

        if not path.exists():
            LOG.debug('Creating path {}', path)

        path.mkdir(parents=True, exist_ok=True)
        return path

    def safely_save(
            self,
            path: str | Path,
            filename: str,
            content: bytes,
    ) -> Path:
        """Save file but not overwrite."""
        path = Path(path)
        old_path = path / filename
        target_path = old_path

        while old_path.exists():
            new_filename = self.make_new_filename(filename)
            new_path = path / new_filename

            if new_path.exists():
                LOG.debug('New name is already taken: {}', new_path)
                continue

            LOG.debug('Renaming {} to {}', old_path, new_filename)
            old_path.replace(new_path)
            break

        LOG.debug('Saving {}', target_path)
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

    @staticmethod
    def get_size(*args: str | Path) -> int | None:
        """Get sze of the file in bytes."""
        try:
            filename = Path().joinpath(*args)
            size = os.stat(filename).st_size
        except OSError:
            size = None
        return size
