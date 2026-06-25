"""Use cases for download-related operations."""

from typing import NamedTuple
from uuid import UUID

from omoide import const
from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase

LOG = custom_logging.get_logger(__name__)


class DownloadResult(NamedTuple):
    """NGINX zip manifest lines plus the item being downloaded and its owner."""

    lines: list[str]
    owner: models.User
    item: models.Item | None


class DownloadCollectionUseCase:
    """Use case for downloading whole group of items as zip archive."""

    def __init__(  # noqa: PLR0913
        self,
        database: AbsDatabase,
        items: db_interfaces.AbsItemsRepo,
        users: db_interfaces.AbsUsersRepo,
        meta: db_interfaces.AbsMetaRepo,
        signatures: db_interfaces.AbsSignaturesRepo,
    ) -> None:
        """Initialize instance."""
        self.database = database
        self.items = items
        self.users = users
        self.meta = meta
        self.signatures = signatures

    async def execute(
        self,
        user: models.User,
        item_uuid: UUID,
    ) -> DownloadResult:
        """Execute."""
        lines: list[str] = []

        async with self.database.transaction() as conn:
            item = await self.items.get_by_uuid(conn, item_uuid)
            owner = await self.users.get_by_id(conn, item.owner_id)
            public_users = await self.users.get_public_user_ids(conn)

            if all(
                (
                    owner.id not in public_users,
                    user.id != owner.id,
                    user.id not in item.permissions,
                )
            ):
                # NOTE - hiding the fact
                msg = 'Item {item_uuid} does not exist'
                raise exceptions.DoesNotExistError(msg, item_uuid=item_uuid)

            children = await self.items.get_children(conn, item)

        async with self.database.transaction() as conn:
            signatures = await self.signatures.get_cr32_signatures_map(
                conn=conn,
                items=children,
            )

            metainfos = await self.meta.get_metainfo_map(conn, children)
            valid_children = [
                child
                for child in children
                if child.content_ext is not None and not child.is_collection
            ]

            total = len(valid_children)
            for i, child in enumerate(valid_children, start=1):
                signature = signatures.get(child.id)
                metainfo = metainfos.get(child.id)

                if signature is None:
                    LOG.warning(
                        'User {} requested download for item {}, but is has no signature',
                        user,
                        item,
                    )

                lines.append(
                    self.form_signature_line(
                        item=child,
                        metainfo=metainfo,
                        signature=signature,
                        current=i,
                        total=total,
                    )
                )

        return DownloadResult(lines=lines, owner=owner, item=item)

    @staticmethod
    def form_signature_line(
        item: models.Item,
        metainfo: models.Metainfo | None,
        signature: int | None,
        current: int,
        total: int,
    ) -> str:
        """Generate signature line for NGINX.

        Example:
        (
            '2caf75ed '
            + '16948 '
            + '/content/content/92b0f.../14/14e0bc....jpg '
            + '7___14e0bc49-8561-4667-8210-202e1965b499.jpg'
        )

        """
        digits = len(str(total))
        template = f'{{:0{digits}d}}'
        owner_uuid = str(item.owner_uuid)
        item_uuid = str(item.uuid)
        base = '/content/content'  # TODO - ensure it is correct path
        prefix = item_uuid[: const.STORAGE_PREFIX_SIZE]
        content_ext = str(item.content_ext)

        fs_path = f'{base}/{owner_uuid}/{prefix}/{item_uuid}.{content_ext}'

        user_visible_filename = f'{template.format(current)}___{item_uuid}.{content_ext}'

        if signature is None:
            checksum = '-'
        else:
            # hash must be converted 123 -> '0x7b' -> '7b
            checksum = hex(signature)[2:]

        size = 0
        if metainfo and metainfo.content_size is not None:
            size = metainfo.content_size

        return f'{checksum} {size} {fs_path} {user_visible_filename}'
