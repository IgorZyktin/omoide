"""Abstract long-term storage for upload content."""

import abc
from collections.abc import AsyncIterable
from typing import Any


class AbsContentStorage(abc.ABC):
    """Long-term storage for content uploaded by users.

    The concrete implementation decides where the bytes live (PostgreSQL
    large object today, S3 tomorrow) and how the worker will find them
    later. ``save()`` returns a small reference dict that the caller
    merges into ``queue_input_media.extras``; the worker reads the same
    extras to retrieve the payload.
    """

    @abc.abstractmethod
    async def save(self, chunks: AsyncIterable[bytes]) -> dict[str, Any]:
        """Stream ``chunks`` into storage and return the reference.

        The returned dict is merged into ``InputMedia.extras`` verbatim,
        so implementations choose their own keys (``{'oid': N}`` for PG,
        ``{'s3_key': '...'}`` for S3, etc.).
        """
