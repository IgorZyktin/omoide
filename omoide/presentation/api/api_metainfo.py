# -*- coding: utf-8 -*-
"""Metainfo related API operations.
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

router = APIRouter(prefix='/api/metainfo')


@router.put('/{uuid}')
async def api_update_metainfo(
        uuid: UUID,
        metainfo_in: api_models.MetainfoIn,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.UpdateMetainfoUseCase = Depends(
            dep.update_metainfo_use_case),
):
    """Update metainfo entry."""
    result = await use_case.execute(policy, user, uuid, metainfo_in)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}


@router.get('/{uuid}')
async def api_read_metainfo(
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ReadMetainfoUseCase = Depends(
            dep.read_metainfo_use_case),
):
    """Get metainfo."""
    result = await use_case.execute(policy, user, uuid)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return result.value
