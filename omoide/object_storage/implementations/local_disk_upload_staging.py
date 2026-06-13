"""Upload staging that writes incoming chunks to a temp file on local disk."""

import asyncio
from collections.abc import AsyncIterable
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import os
from pathlib import Path
import tempfile

from omoide.object_storage.interfaces.abs_upload_staging import AbsStagedFile
from omoide.object_storage.interfaces.abs_upload_staging import AbsUploadStaging


class _LocalStagedFile(AbsStagedFile):
    """``AbsStagedFile`` backed by a temp file on the local filesystem."""

    def __init__(self, path: Path, size: int) -> None:
        """Initialize instance."""
        self._path = path
        self._size = size

    @property
    def size(self) -> int:
        """Return the total number of bytes that were streamed in."""
        return self._size

    async def read_all(self) -> bytes:
        """Load the full file into memory."""
        return await asyncio.to_thread(self._path.read_bytes)

    async def iter_chunks(self, chunk_size: int) -> AsyncIterator[bytes]:
        """Yield the file content as chunks."""
        if chunk_size <= 0:
            msg = 'chunk_size must be positive'
            raise ValueError(msg)

        fobj = await asyncio.to_thread(self._path.open, 'rb')
        try:
            while True:
                chunk = await asyncio.to_thread(fobj.read, chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            await asyncio.to_thread(fobj.close)


class LocalDiskUploadStaging(AbsUploadStaging):
    """Stage uploads as temp files on local disk.

    The temp file lives only for the duration of the ``stage()`` context
    manager. ``folder`` controls where the file is created; when ``None``
    the system temp directory is used.
    """

    def __init__(self, folder: Path | None = None, chunk_size: int = 1024 * 1024) -> None:
        """Initialize instance."""
        if chunk_size <= 0:
            msg = 'chunk_size must be positive'
            raise ValueError(msg)
        self.folder = folder
        self.chunk_size = chunk_size
        if folder is not None:
            folder.mkdir(parents=True, exist_ok=True)

    @asynccontextmanager
    async def stage(self, source: AsyncIterable[bytes]) -> AsyncIterator[AbsStagedFile]:
        """Stream ``source`` into a temp file and yield a handle to it."""
        dir_str = str(self.folder) if self.folder is not None else None
        fd, path_str = await asyncio.to_thread(
            tempfile.mkstemp, prefix='omoide-upload-', dir=dir_str
        )
        path = Path(path_str)
        size = 0
        try:
            fobj = os.fdopen(fd, 'wb')
            try:
                async for chunk in source:
                    if not chunk:
                        continue
                    size += len(chunk)
                    await asyncio.to_thread(fobj.write, chunk)
            finally:
                await asyncio.to_thread(fobj.close)

            yield _LocalStagedFile(path, size)
        finally:
            await asyncio.to_thread(path.unlink, missing_ok=True)
