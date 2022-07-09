# -*- coding: utf-8 -*-
"""Media related API operations.
"""
import http
from uuid import UUID

from fastapi import HTTPException, Depends, APIRouter

from omoide import domain, use_cases
from omoide.domain import exceptions
from omoide.presentation import api_models
from omoide.presentation import dependencies as dep

router = APIRouter(prefix='/api/media')


@router.put('/{uuid}/{media_type}')
async def api_create_or_update_media(
        uuid: UUID,
        media_type: str,
        media_in: api_models.CreateMediaIn,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.CreateOrUpdateMediaUseCase = Depends(
            dep.update_media_use_case),
):
    """Create or update media entry."""
    try:
        await use_case.execute(user, uuid, media_type, media_in)
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    return 'ok'


@router.get('/{uuid}/{media_type}')
async def api_read_media(
        uuid: UUID,
        media_type: str,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.ReadMediaUseCase = Depends(
            dep.read_media_use_case),
):
    """Get media."""
    try:
        media = await use_case.execute(user, uuid, media_type)
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))
    return media.dict()


@router.delete('/{uuid}/{media_type}')
async def api_delete_media(
        uuid: UUID,
        media_type: str,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.DeleteMediaUseCase = Depends(
            dep.delete_media_use_case),
):
    """Delete media.

    If media does not exist return 404.
    If media was successfully deleted, 200.
    """
    try:
        await use_case.execute(user, uuid, media_type)
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))
    return 'ok'
