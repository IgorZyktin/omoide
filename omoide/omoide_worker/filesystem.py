"""Special class that works with filesystem."""

import os.path
from pathlib import Path
from typing import Iterator
from uuid import UUID

from omoide import utils
from omoide import custom_logging
from omoide.omoide_worker.worker_config import Config

LOG = custom_logging.get_logger(__name__)


class Filesystem:
    """Special class that works with filesystem."""

    def __init__(self, config: Config) -> None:
        """Initialize instance."""
        self._config = config

    def _get_folders(self) -> Iterator[Path]:
        """Return all folders where we plan to save/load anything."""
        if self._config.save_hot and self._config.hot_folder:
            yield self._config.hot_folder
        if self._config.save_cold and self._config.cold_folder:
            yield self._config.cold_folder

    def load_binary(
        self,
        owner_uuid: UUID,
        item_uuid: UUID,
        media_type: str,
        ext: str,
    ) -> bytes:
        """Load binary data from filesystem."""
        bucket = utils.get_bucket(item_uuid, self._config.prefix_size)
        for folder in self._get_folders():
            path = (
                Path(folder)  # noqa: W503
                / media_type  # noqa: W503
                / str(owner_uuid)  # noqa: W503
                / bucket  # noqa: W503
                / f"{item_uuid}.{ext}" # noqa: W503
            )  # noqa: W503

            if path.exists():
                content = path.read_bytes()
                return content

        msg = (
            f"There is no corresponding file in folder {media_type} "
            f"for {owner_uuid=}, {item_uuid=} and {ext=}"
        )
        raise FileNotFoundError(msg)

    def save_binary(
        self,
        owner_uuid: UUID,
        item_uuid: UUID,
        media_type: str,
        ext: str,
        content: bytes,
    ) -> None:
        """Save binary data to filesystem."""
        bucket = utils.get_bucket(item_uuid, self._config.prefix_size)
        filename = f"{item_uuid}.{ext}"
        for folder in self._get_folders():
            path = (
                Path(folder)  # noqa: W503
                / media_type  # noqa: W503
                / str(owner_uuid)  # noqa: W503
                / bucket  # noqa: W503
            )  # noqa: W503

            self.ensure_folder_exists(path)
            self.safely_save(path, filename, content)

    @staticmethod
    def ensure_folder_exists(path: Path) -> bool:
        """Create folder if needed."""
        created = False

        if not path.exists():
            LOG.debug("Creating path {}", path)
            created = True

        path.mkdir(parents=True, exist_ok=True)
        return created

    def safely_save(
        self,
        path: Path,
        filename: str,
        content: bytes,
    ) -> Path:
        """Save file but not overwrite."""
        old_path = path / filename
        target_path = old_path

        while old_path.exists():
            new_filename = self.make_new_filename(filename)
            new_path = path / new_filename

            if new_path.exists():
                LOG.debug("New name is already taken: {}", new_path)
                continue

            LOG.debug("Renaming {} to {}", old_path, new_filename)
            old_path.replace(new_path)
            break

        LOG.debug("Saving {}", target_path)
        target_path.write_bytes(content)
        return target_path

    @staticmethod
    def make_new_filename(filename: str, separator: str = "___") -> str:
        """Generate new name using old name."""
        name, ext = os.path.splitext(filename)
        left_segment, *_ = name.split(separator)
        moment = utils.now().isoformat()
        return f"{left_segment}{separator}{moment}{ext}"
