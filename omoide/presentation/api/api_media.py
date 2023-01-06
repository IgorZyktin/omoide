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


@router.post('/{uuid}')
async def api_create_media(
        uuid: UUID,
        media_in: list[api_models.CreateMediaIn],
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.CreateMediaUseCase = Depends(
            dep.create_media_use_case),
):
    """Create or update media entry."""
    result = await use_case.execute(policy, user, uuid, media_in)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}
