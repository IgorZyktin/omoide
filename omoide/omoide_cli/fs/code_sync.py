"""Implementation for sync filesystem command."""

from functools import cached_property
from pathlib import Path
import shutil
from uuid import UUID

from omoide import const
from omoide import custom_logging
from omoide import utils

LOG = custom_logging.get_logger(__name__)


async def sync(  # noqa: C901, PLR0912
    main_folder: Path,
    replica_folder: Path,
    only_users: list[UUID] | None,
    verbose: bool,
    dry_run: bool,
    limit: int,
) -> int:
    """Synchronize files in different content folders."""
    main = Origin(
        folder=main_folder,
        prefix_size=const.STORAGE_PREFIX_SIZE,
        verbose=verbose,
        dry_run=dry_run,
    )

    replica = Origin(
        folder=replica_folder,
        prefix_size=const.STORAGE_PREFIX_SIZE,
        verbose=verbose,
        dry_run=dry_run,
    )

    sequence = [const.CONTENT, const.PREVIEW, const.THUMBNAIL]
    total_operations = 0
    total_items = 0

    LOG.info('Synchronizing users')

    for target in sequence:
        LOG.info('Checking {} for user sync', target)
        total_operations += main.ensure_target(target)
        total_operations += replica.ensure_target(target)

        main_branch = getattr(main, target)
        replica_branch = getattr(replica, target)

        for user in main_branch.users:
            if only_users is not None and user.uuid not in only_users:
                continue

            replica_uuids = {user.uuid for user in replica_branch.users}

            if user.uuid not in replica_uuids:
                total_operations += 1
                src = main.folder / target / str(user.uuid)
                dst = replica.folder / target / str(user.uuid)

                if dry_run:
                    LOG.warning('Will copy {} to {}', src, dst)
                else:
                    LOG.warning('Copying {} to {}', src, dst)
                    shutil.copytree(
                        src=str(src.absolute()),
                        dst=str(dst.absolute()),
                    )

    LOG.info('Synchronizing items')

    for target in sequence:
        LOG.info('Checking {} for item sync', target)
        main_branch = getattr(main, target)
        replica_branch = getattr(replica, target)

        for main_user in main_branch.users:
            if only_users is not None and main_user.uuid not in only_users:
                continue

            replica_user = replica_branch.get_user(main_user.uuid)
            diff = set(main_user.items) - set(replica_user.items)

            for item in diff:
                src = main.folder / target / str(main_user.uuid) / item.path
                dst = replica.folder / target / str(replica_user.uuid) / item.path

                if dry_run:
                    LOG.warning('Will copy {} to {}', src, dst)
                else:
                    LOG.warning('Copying {} to {}', src, dst)
                    shutil.copytree(
                        src=str(src.absolute()),
                        dst=str(dst.absolute()),
                    )

                total_operations += 1
                total_items += 1

                if total_items >= limit != -1:
                    return total_operations

    return total_operations


class Item:
    """Helper type that represents item-level-folder."""

    def __init__(self, prefix: str, name: str) -> None:
        """Initialize instance."""
        self.prefix = prefix
        self.name = name

    def __repr__(self) -> str:
        """Return textual representation."""
        return f'<Item {self.path}>'

    def __eq__(self, other: object) -> bool:
        """Return True if we have the same item."""
        if isinstance(other, Item):
            return self.prefix == other.prefix and self.name == other.name
        return False

    def __hash__(self) -> int:
        """Return hash for filename."""
        return hash((self.prefix, self.name))

    @property
    def path(self) -> Path:
        """Return combined path for the item."""
        return Path(self.prefix) / f'{self.name}'


class User:
    """Helper type that represents user-level-folder."""

    def __init__(self, uuid: UUID, folder: Path) -> None:
        """Initialize instance."""
        self.uuid = uuid
        self.folder = folder

    def __repr__(self) -> str:
        """Return textual representation."""
        return f'<User {self.uuid}>'

    @cached_property
    def items(self) -> list[Item]:
        """Return all top level folders."""
        items: list[Item] = []

        if not self.folder.exists():
            return items

        for prefix in self.folder.iterdir():
            for file in prefix.iterdir():
                if file.is_file():
                    items.append(Item(prefix=prefix.name, name=file.name))

        return items


class Origin:
    """Helper type that processes filesystem trees."""

    def __init__(
        self,
        folder: Path,
        prefix_size: int,
        *,
        verbose: bool,
        dry_run: bool,
    ) -> None:
        """Initialize instance."""
        self.folder = folder
        self.prefix_size = prefix_size
        self.verbose = verbose
        self.dry_run = dry_run

        self.content = OriginBranch(self, 'content')
        self.preview = OriginBranch(self, 'preview')
        self.thumbnail = OriginBranch(self, 'thumbnail')

    def ensure_target(self, target: str) -> int:
        """Create top-level folder if need to."""
        total = 0
        if not (main_target := (self.folder / target)).exists():
            total += 1
            if self.dry_run:
                LOG.warning('Will create folder {}', main_target)
            else:
                main_target.mkdir()
        return total


class OriginBranch:
    """Implementation for specific folder."""

    def __init__(self, origin: Origin, directory: str) -> None:
        """Initialize instance."""
        self.origin = origin
        self.directory = directory
        self.root = self.origin.folder / directory

    @cached_property
    def users(self) -> list[User]:
        """Return all top level folders."""
        users: list[User] = []

        if not self.root.exists():
            return users

        for folder in self.root.iterdir():
            if folder.is_dir() and utils.is_valid_uuid(folder.name):
                users.append(User(uuid=UUID(folder.name), folder=folder))

        return users

    def get_user(self, user_uuid: UUID) -> User:
        """Return user with current UUID."""
        for user in self.users:
            if user.uuid == user_uuid:
                return user

        msg = f'There is no user with UUID {user_uuid} in {self.directory}'
        raise RuntimeError(msg)
