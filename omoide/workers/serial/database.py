"""Database for serial operations."""

from omoide.workers.common.base_db import BaseWorkerDatabase
from omoide.workers.serial.cfg import Config


class SerialDatabase(BaseWorkerDatabase[Config]):
    """Database for serial operations."""
