"""Abstract staging area for streaming uploads."""

import abc
from collections.abc import AsyncIterable
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager


class AbsStagedFile(abc.ABC):
    """Handle to a file that has been streamed into a staging area.

    The backing storage is opaque to the caller: it may be a temp file
    on local disk, an object in S3, or anything else that the concrete
    ``AbsUploadStaging`` implementation chose. Callers MUST treat the
    handle as valid only inside the ``stage()`` context manager that
    produced it.
    """

    @property
    @abc.abstractmethod
    def size(self) -> int:
        """Return the total number of bytes that were streamed in."""

    @abc.abstractmethod
    async def read_all(self) -> bytes:
        """Load the full file into memory.

        Use only when the size is known to fit in memory (e.g. when it
        is below the threshold that decides between inline storage and
        a large-object reference).
        """

    @abc.abstractmethod
    def iter_chunks(self, chunk_size: int) -> AsyncIterator[bytes]:
        """Yield the file content as chunks for streaming consumers."""


class AbsUploadStaging(abc.ABC):
    """Abstract staging area for files that are uploaded in chunks.

    Concrete implementations stream incoming chunks somewhere (local
    disk today, S3 in the future) and yield a handle that downstream
    code can interrogate without holding the whole payload in memory.
    """

    @abc.abstractmethod
    def stage(
        self,
        source: AsyncIterable[bytes],
    ) -> AbstractAsyncContextManager[AbsStagedFile]:
        """Stream ``source`` into staging and yield a handle to the staged file.

        The handle is valid only inside the returned context manager;
        any temp resources it allocated are released on exit.
        """
