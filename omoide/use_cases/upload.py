# -*- coding: utf-8 -*-
"""Use case for media upload.
"""
import datetime
from uuid import UUID

from omoide import domain
from omoide.domain import interfaces, exceptions
from omoide.presentation import api_models


class UploadUseCase:
    """Use case for media upload."""

    def __init__(self, repo: interfaces.AbsUploadRepository) -> None:
        """Initialize instance."""
        self._repo = repo

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
            is_collection: bool,
            files: list,
            tags: list[str],
            permissions: list[str],
            features: list[str],
    ) -> list[UUID]:
        """Return preview model suitable for rendering."""
        if user.is_anon():
            raise exceptions.Unauthorized('Anon users are not '
                                          'allowed to make uploads')

        created_uuids: list[UUID] = []
        async with self._repo.transaction():
            await self._repo.assert_has_access(user, uuid, only_for_owner=True)

            if is_collection:
                for file in files:
                    filename = file.filename.lower()
                    content = await file.read()

                    if content:
                        child_item = await self._generate_item(
                            user=user,
                            parent_uuid=uuid,
                            tags=tags,
                            permissions=permissions,
                            filename=filename,
                        )

                        await self._upload_media_content(
                            uuid=child_item,
                            filename=filename,
                            content=content,
                            features=features,
                        )
                        created_uuids.append(child_item)
            else:
                content = await files[0].read()

                if content:
                    await self._upload_media_content(
                        uuid=uuid,
                        filename=files[0].filename.lower(),
                        content=content,
                        features=features,
                    )

        return created_uuids

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

        # TODO: do not use filename as item name!
        payload = api_models.CreateItemIn(
            uuid=uuid,
            parent_uuid=parent_uuid,
            name=filename,
            is_collection=False,
            tags=tags,
            permissions=permissions,
        )

        await self._repo.create_item(user, payload)
        return uuid

    async def _upload_media_content(
            self,
            uuid: UUID,
            filename: str,
            content: bytes,
            features: list[str],
    ) -> bool:
        """Upload media to existing item."""
        raw_media = domain.RawMedia(
            uuid=uuid,
            created_at=datetime.datetime.now(tz=datetime.timezone.utc),
            processed_at=None,
            status='init',
            filename=filename,
            content=content,
            features=features,
            signature='',  # TODO: add actual signature calculation
        )
        await self._repo.save_raw_media(raw_media)
        return True
