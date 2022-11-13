# -*- coding: utf-8 -*-
"""Helper data structures for resource counting.
"""
from collections import defaultdict
from functools import cached_property
from pathlib import Path
from uuid import UUID


class UserData:
    """User container."""

    def __init__(self, uuid: UUID, name: str):
        """Initialize instance."""
        self.uuid = uuid
        self.name = name
        self.files: dict[str, int] = defaultdict(int)
        self.bytes: dict[str, int] = defaultdict(int)

    def __repr__(self) -> str:
        """Return string representation."""
        return f'<{self.uuid}:{self.name!r}>'

    def store_size(
            self,
            path: Path,
            size: int,
    ) -> None:
        """Save file size."""
        prefix = path.name
        self.files[prefix] += 1
        self.bytes[prefix] += size

    def size_per_prefix(self, prefix: str) -> int:
        """Return size of the prefix group."""
        return self.bytes[prefix]

    @cached_property
    def total_size(self) -> int:
        """Return total size."""
        return sum(self.bytes.values())


class Stats:
    """Helper data structure for resource counting."""

    def __init__(self):
        """Initialize instance."""
        self.users: dict[UUID, UserData] = {}

    def store_user(self, uuid: UUID, name: str) -> None:
        """Save user in stats."""
        if uuid in self.users:
            return

        self.users[uuid] = UserData(uuid, name)

    def store_size(
            self,
            uuid: UUID,
            path: Path,
            file: Path,
            size: int,
    ) -> None:
        """Save file size."""
        user = self.users.get(uuid)

        if user is None:
            print(f'Cannot find user {uuid} for entry {str(file)}')
            return

        user.store_size(path, size)
