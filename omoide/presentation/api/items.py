# -*- coding: utf-8 -*-
"""Item related API operations.
"""
import http
from uuid import UUID

from fastapi import HTTPException, Response, Depends, APIRouter, Request

from omoide import domain, use_cases
from omoide.domain import exceptions
from omoide.presentation import api_models
from omoide.presentation import dependencies as dep

router = APIRouter(prefix='/api/items')


@router.post(
    '',
    status_code=http.HTTPStatus.CREATED,
    response_model=api_models.OnlyUUID,
)
async def api_create_item(
        request: Request,
        response: Response,
        payload: api_models.CreateItemIn,
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
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))

    response.headers['Location'] = request.url_for('api_read_item', uuid=uuid)
    return api_models.OnlyUUID(uuid=uuid)


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


@router.patch('/{uuid}')
async def api_partial_update_item(
        uuid: UUID,
        operations: list[api_models.PatchOperation],
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.UpdateItemUseCase = Depends(
            dep.update_item_use_case),
):
    """Update item."""
    try:
        await use_case.execute(user, uuid, operations)
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))
    return api_models.OnlyUUID(uuid=uuid)


@router.delete(
    '/{uuid}',
    response_model=api_models.OnlyUUID,
)
async def api_delete_item(
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.DeleteItemUseCase = Depends(
            dep.delete_item_use_case),
):
    """Delete item.

    If item does not exist return 404.

    If item was successfully deleted, return UUID of the parent
    (so you could browse which items are still exist in this collection).
    """
    try:
        uuid = await use_case.execute(user, uuid)
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))

    return api_models.OnlyUUID(uuid=uuid)
