# -*- coding: utf-8 -*-
"""Metainfo related API operations.
"""
import http
from uuid import UUID

from fastapi import HTTPException, Depends, APIRouter

from omoide import domain, use_cases
from omoide.domain import exceptions
from omoide.presentation import api_models
from omoide.presentation import dependencies as dep

router = APIRouter(prefix='/api/meta')


@router.put('/{uuid}')
async def api_create_or_update_meta(
        uuid: UUID,
        meta_in: api_models.MetaIn,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.CreateOrUpdateMetaUseCase = Depends(
            dep.update_meta_use_case),
):
    """Create or update meta entry."""
    try:
        await use_case.execute(user, uuid, meta_in)
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    return 'ok'


@router.get('/{uuid}')
async def api_read_meta(
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.ReadMetaUseCase = Depends(
            dep.read_meta_use_case),
):
    """Get meta."""
    try:
        media = await use_case.execute(user, uuid)
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))
    return media.dict()
