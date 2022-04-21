# -*- coding: utf-8 -*-
"""Use case for media upload.
"""
from uuid import UUID

from omoide import domain
from omoide.domain import interfaces


class UploadUseCase:
    """Use case for media upload."""

    def __init__(self, repo: interfaces.AbsItemCRUDRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: domain.User,
            item_uuid: UUID,
            is_collection: bool,
            files: list,
            tags: list[str],
            permissions: list[str],
            features: list[str],
    ) -> tuple[domain.AccessStatus, list[UUID]]:
        """Return preview model suitable for rendering."""
        created_uuids: list[UUID] = []
        async with self._repo.transaction():
            access = await self._repo.check_access(user, str(item_uuid))

            if access.is_given:
                if is_collection:
                    for file in files:
                        content = await file.read()

                        if content:
                            child_item = await self._generate_item(
                                user=user,
                                parent_uuid=item_uuid,
                                tags=tags,
                                permissions=permissions,
                                filename=file.filename,
                            )

                            await self._upload_media_content(
                                uuid=child_item,
                                content=content,
                                features=features,
                            )
                            created_uuids.append(child_item)
                else:
                    content = await files[0].read()

                    if content:
                        await self._upload_media_content(
                            uuid=item_uuid,
                            content=content,
                            features=features,
                        )

        return access, created_uuids

    async def _generate_item(
            self,
            user: domain.User,
            parent_uuid: UUID,
            tags: list[str],
            permissions: list[str],
            filename: str,
    ) -> UUID:
        """Create child item for given target and return uuid."""
        uuid = await self._repo.generate_uuid()

        payload = domain.CreateItemPayload(
            uuid=uuid,
            parent_uuid=str(parent_uuid),
            item_name=filename,
            is_collection=False,
            tags=tags,
            permissions=permissions,
        )

        await self._repo.create_dependant_item(user, payload)
        return uuid

    async def _upload_media_content(
            self,
            uuid: UUID,
            content: bytes,
            features: list[str],
    ) -> bool:
        """Upload media to existing item."""
        print(content)
        # TODO
        return True
