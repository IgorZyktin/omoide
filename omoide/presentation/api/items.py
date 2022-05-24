# -*- coding: utf-8 -*-
"""Item related API operations.
"""
import http
from uuid import UUID

from fastapi import HTTPException, Response, Depends, APIRouter, Request

from omoide import domain, use_cases
from omoide.domain import exceptions
from omoide.presentation import dependencies as dep

router = APIRouter(prefix='/api/items')


@router.post('', status_code=http.HTTPStatus.CREATED)
async def api_create_item(
        request: Request,
        response: Response,
        payload: domain.CreateItemIn,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.CreateItemUseCase = Depends(
            dep.create_item_use_case),
):
    """Create item."""
    try:
        uuid = await use_case.execute(user, payload)
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))

    response.headers['Location'] = request.url_for('api_read_item', uuid=uuid)

    if payload.is_collection:
        url = request.url_for('browse', uuid=uuid)
    else:
        url = request.url_for('preview', uuid=uuid)

    upload_url = request.url_for('upload') + f'?parent_uuid={uuid}'

    return {
        'url': url,
        'upload_url': upload_url,
    }


@router.get('/{uuid}')
async def api_read_item(
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.ReadItemUseCase = Depends(
            dep.read_item_use_case),
):
    """Get item."""
    try:
        item = await use_case.execute(user, uuid)
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))
    return item.dict()


@router.get('/{uuid}')
async def api_update_item(
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.UploadUseCase = Depends(
            dep.read_item_use_case),
):
    """Update item."""
    # TODO(i.zyktin): implement item update
    assert uuid
    assert user
    assert use_case
    return 'not implemented'


@router.delete('/{uuid}')
async def api_delete_item(
        request: Request,
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.DeleteItemUseCase = Depends(
            dep.delete_item_use_case),
):
    """Delete item."""
    try:
        parent_item = await use_case.execute(user, uuid)
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))

    if parent_item is None:
        url = None
    elif parent_item.is_collection:
        url = request.url_for('browse', uuid=parent_item.uuid)
    else:
        url = request.url_for('preview', uuid=parent_item.uuid)

    return {
        'url': url,
    }
