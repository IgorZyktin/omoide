# -*- coding: utf-8 -*-
"""Use case for Meta.
"""
from datetime import datetime, timezone
from uuid import UUID

from omoide import domain, utils
from omoide.domain import interfaces, exceptions
from omoide.presentation import api_models

__all__ = [
    'CreateOrUpdateMetaUseCase',
    'ReadMetaUseCase',
]


class BaseMetaUseCase:
    """Base use case."""

    def __init__(
            self,
            items_repo: interfaces.AbsItemsRepository,
            meta_repo: interfaces.AbsMetaRepository,
    ) -> None:
        """Initialize instance."""
        self.items_repo = items_repo
        self.meta_repo = meta_repo

    async def _assert_has_access(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> domain.AccessStatus:
        """Raise if user has no access to this Meta."""
        access = await self.items_repo.check_access(user, uuid)

        if access.does_not_exist:
            raise exceptions.NotFound(f'Item {uuid} does not exist')

        if access.is_not_given:
            raise exceptions.Forbidden(f'User {user.uuid} ({user.name}) '
                                       f'has no access to item {uuid}')

        if access.is_not_owner:
            raise exceptions.Forbidden(f'You must own item {uuid} '
                                       'to be able to modify it')

        return access


class CreateOrUpdateMetaUseCase(BaseMetaUseCase):
    """Use case for updating Meta."""

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
            meta_in: api_models.MetaIn,
    ) -> bool:
        """Business logic."""
        await self._assert_has_access(user, uuid)
        # TODO - extend with more detailed info

        meta = domain.Meta(
            item_uuid=uuid,
            meta={
                'registered_on': str(utils.now()),
                'type': meta_in.file_type,
                'size': meta_in.file_size,
                'original_file_name': meta_in.original_file_name,
                'original_file_modified_at': meta_in.original_file_modified_at,
            },
        )

        return await self.meta_repo.create_or_update_meta(user, meta)


class ReadMetaUseCase(BaseMetaUseCase):
    """Use case for getting Meta."""

    async def execute(
            self,
            user: domain.User,
            uuid: UUID,
    ) -> domain.Meta:
        await self._assert_has_access(user, uuid)
        exif = await self.meta_repo.read_meta(uuid)

        if exif is None:
            raise exceptions.NotFound(f'Meta {uuid} does not exist')

        return exif
