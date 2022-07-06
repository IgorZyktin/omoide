# -*- coding: utf-8 -*-
"""Media related API operations.
"""
import http
from uuid import UUID

from fastapi import HTTPException, Response, Depends, APIRouter, Request

from omoide import domain, use_cases
from omoide.domain import exceptions
from omoide.presentation import api_models
from omoide.presentation import dependencies as dep

router = APIRouter(prefix='/api/media')


@router.put(
    '/{uuid}',
    response_model=api_models.OnlyUUID,
)
async def api_create_or_update_media(
        uuid: UUID,
        request: Request,
        response: Response,
        payload: api_models.CreateMediaIn,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.CreateOrUpdateMediaUseCase = Depends(
            dep.update_media_use_case),
):
    """Create or update media entry."""
    try:
        created = await use_case.execute(user, uuid, payload)
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))

    response.headers['Location'] = request.url_for('api_read_media', uuid=uuid)

    if created:
        response.status_code = http.HTTPStatus.CREATED
    else:
        response.status_code = http.HTTPStatus.OK

    return response


@router.get('/{uuid}')
async def api_read_media(
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.ReadMediaUseCase = Depends(
            dep.read_media_use_case),
):
    """Get media."""
    try:
        media = await use_case.execute(user, uuid)
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))
    return media.dict()


@router.delete('/{uuid}')
async def api_delete_media(
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.DeleteMediaUseCase = Depends(
            dep.delete_media_use_case),
):
    """Delete media.

    If media does not exist return 404.
    If media was successfully deleted, 200.
    """
    try:
        await use_case.execute(user, uuid)
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))
    return 'ok'
