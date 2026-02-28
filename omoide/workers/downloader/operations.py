"""Download operations."""

from omoide import models
from omoide.workers.downloader.cfg import WorkerDownloaderConfig
from omoide.workers.downloader.database import DownloaderPostgreSQLDatabase


def download_media(
    config: WorkerDownloaderConfig,
    database: DownloaderPostgreSQLDatabase,
    model: models.OutputMedia,
) -> None:
    """Download to a file."""
    print(model)
