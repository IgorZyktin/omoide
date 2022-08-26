# -*- coding: utf-8 -*-
"""Media related API operations.
"""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends

from omoide import domain
from omoide import use_cases
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.presentation import api_models
from omoide.presentation import dependencies as dep
from omoide.presentation import web

router = APIRouter(prefix='/api/media')


@router.put('/{uuid}/{media_type}')
async def api_create_or_update_media(
        uuid: UUID,
        media_type: str,
        media_in: api_models.CreateMediaIn,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.CreateOrUpdateMediaUseCase = Depends(
            dep.update_media_use_case),
):
    """Create or update media entry."""
    result = await use_case.execute(policy, user, uuid, media_type, media_in)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}


@router.get('/{uuid}/{media_type}')
async def api_read_media(
        uuid: UUID,
        media_type: str,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ReadMediaUseCase = Depends(
            dep.read_media_use_case),
):
    """Get media."""
    result = await use_case.execute(policy, user, uuid, media_type)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return result.value


@router.delete('/{uuid}/{media_type}')
async def api_delete_media(
        uuid: UUID,
        media_type: str,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.DeleteMediaUseCase = Depends(
            dep.delete_media_use_case),
):
    """Delete media.

    If media does not exist return 404.
    If media was successfully deleted, 200.
    """
    result = await use_case.execute(policy, user, uuid, media_type)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}
